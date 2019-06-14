
# Native libraries
import sqlite3
import json
import logging
import traceback
import atexit
from threading import Lock
from typing import List

# Package modules
from .assets import Stop
from .helpers import current_timestamp
from .exceptions import *


logger = logging.getLogger("pybuses.sqlite")
log = logger


"""STRUCTURE OF SQLite3 DATABASE used by PyBuses
The database only helds Stop data, including Google Maps & StreetView related data

Table: stops
Columns:
- id: integer primary key
- name: text not null
- lat: float default null
- lon: float default null
- other: text default null
- saved: integer
- updated: integer

"""

# TODO Field "Other" should be another table instead of JSON-String
_STOPS_TABLE_CREATE = """CREATE TABLE IF NOT EXISTS stops(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    lat FLOAT DEFAULT NULL,
    lon FLOAT DEFAULT NULL,
    other TEXT DEFAULT NULL,
    saved INTEGER NOT NULL,
    updated INTEGER NOT NULL
)"""
# noinspection SqlResolve
_FIND_STOP = """SELECT name, lat, lon, other, saved, updated FROM stops WHERE id=?"""
# noinspection SqlResolve
_IS_STOP_SAVED = """SELECT COUNT(id) FROM stops WHERE id=?"""
# noinspection SqlResolve
_SAVE_STOP_NEW = """INSERT INTO stops(
    id, name, lat, lon, other, saved, updated
) VALUES (?,?,?,?,?,?,?)"""
# noinspection SqlResolve
_SAVE_STOP_UPDATE = """UPDATE stops SET
    name=?,
    lat=?,
    lon=?,
    other=?,
    updated=?
WHERE id=?
"""
# noinspection SqlResolve
_DELETE_STOP = """DELETE FROM stops WHERE id=?"""
# noinspection SqlResolve
_GET_ALL_STOP_IDS = """SELECT id FROM stops"""


class SqliteDB(object):
    def __init__(self, filename):
        """
        :param filename: Name or path of the file where the Sqlite DB is located or will be created
        :raise: Sqlite3 exceptions
        """
        self.filename = filename
        self.lock = Lock()
        # noinspection PyTypeChecker
        self.db: sqlite3.Connection = None

        # Connect to Sqlite3 DB
        try:
            self.connect()
        except sqlite3.DatabaseError as ex:
            log.critical(f"Could not connect to Sqlite3 DB:\n{ex}")
            self.disconnect()
        else:
            atexit.register(self.disconnect)

        # Alias
        self.close = self.disconnect

    def connect(self):
        """Connect to the Sqlite database. Sqlite3 Connection instance is saved on self.db.
        Stops table is automatically created on the database if it does not exist.
        :raise: Sqlite3 exceptions
        """
        # log.debug(f"Connecting to Sqlite3 DB {self.filename} and creating tables...")
        self.db = sqlite3.connect(self.filename, check_same_thread=False)
        cursor = self.db.cursor()
        cursor.execute(_STOPS_TABLE_CREATE)
        self.db.commit()
        cursor.close()
        log.info(f"Sqlite3 DB {self.filename} connected")

    def disconnect(self):
        if isinstance(self.db, sqlite3.Connection):
            # log.debug(f"Closing Sqlite3 DB {self.filename}, currently connected")
            try:
                self.db.close()
            except sqlite3.Error:
                log.warning(f"Error while closing Sqlite3 DB, but ignored:\n{traceback.format_exc()}")
            self.db = None
            log.info(f"SQLite3 DB {self.filename} closed")

    def find_stop(self, stopid: int) -> Stop:
        """Search a Stop on the Sqlite database by the StopID.
        This method is used as a StopGetter function of PyBuses.
        :param stopid: ID of the Stop to search
        :type stopid: int
        :return: found Stop object
        :rtype: Stop
        :raise: StopNotFound or StopGetterUnavailable
        """
        try:
            # log.debug(f"Searching Stop ID #{stopid} on Sqlite3 DB")
            cursor = self.db.cursor()
            cursor.execute(_FIND_STOP, (stopid,))
            result = cursor.fetchone()
            cursor.close()
        except sqlite3.DatabaseError as ex:
            log.error(f"Error while searching Stop ID #{stopid} on Sqlite3 DB:\n{traceback.format_exc()}")
            raise StopGetterUnavailable(f"Error on Sqlite database:\n{ex}")
        if not result:
            log.debug(f"Stop ID #{stopid} not found on Sqlite3 DB")
            raise StopNotFound(f"Stop not found on this Sqlite database")
        else:
            # name, lat, lon, other, saved, updated
            stop = Stop(stopid, result[0])
            lat, lon = result[1], result[2]
            if lat and lon:
                stop.lat, stop.lon = lat, lon
            other = result[3]
            saved = result[4]
            updated = result[5]
            if type(other) is str:
                other = json.loads(other.replace("'", '"'))
                keys = other.keys()
                # If Stop in DB has 'saved' and/or 'update' attributes used by something else,
                # replace them starting with '_saved', '_updated'
                if "saved" in keys:
                    other["_saved"] = other.pop("saved")
                if "updated" in keys:
                    other["_updated"] = other.pop("updated")
            else:
                other = dict()
            other["saved"] = saved
            other["updated"] = updated
            stop.other = other
            log.debug(f"Found Stop ID #{stopid} on Sqlite3 DB (name='{stop.name}', location={stop.lat}, {stop.lon})")
            return stop

    def is_stop_saved(self, stopid: int) -> bool:
        """Check if the given Stop is saved on the database.
        :param stopid: ID of the Stop to search
        :type stopid: int
        :return: True if Stop is saved, False if not found on database
        :rtype: bool
        :raise: Sqlite3 exceptions
        """
        cursor = self.db.cursor()
        cursor.execute(_IS_STOP_SAVED, (stopid,))
        result = cursor.fetchone()[0]
        cursor.close()
        result = bool(result)
        log.debug(f"Checked if Stop ID #{stopid} is saved on Sqlite3 DB: Result: {result}")
        return result

    def save_stop(self, stop: Stop, update: bool = True):
        """Save or update a Stop on this Sqlite DB.
        If update=True and the stop is currently saved, it will be updated with the Stop provided.
        This method is used as a StopSetter function of PyBuses.
        :param stop: The Stop to save, with all the available information completed (at least ID and Name are required)
        :param update: if True, when the Stop to save exists in database, update it with the Stop provided
        :type stop: Stop
        :type update: bool
        :raise: StopSetterUnavailable
        """
        try:
            saved = self.is_stop_saved(stop.stopid)
            other = stop.other
            # Remove 'saved' and 'deleted' keys from Other dict
            if type(other) is dict:
                keys = other.keys()
                if "saved" in keys:
                    other.pop("saved")
                if "updated" in keys:
                    other.pop("updated")
                other = str(other)
            else:
                other = None
            if not saved:
                # Stop not currently saved on DB, and save it
                query = _SAVE_STOP_NEW
                # id, name, lat, lon, other, saved, updated
                now = current_timestamp()
                variables = (
                    stop.stopid,
                    stop.name,
                    stop.lat,
                    stop.lon,
                    other,
                    now,
                    now
                )
                log.info(f"Saved Stop ID #{stop.stopid} ({stop.name}) on Sqlite3 DB")
            elif saved and update:
                # Stop currently saved, and update it
                query = _SAVE_STOP_UPDATE
                # name, lat, lon, other, updated, id
                variables = (
                    stop.name,
                    stop.lat,
                    stop.lon,
                    other,
                    current_timestamp(),
                    stop.stopid
                )
                log.info(f"Updated Stop ID #{stop.stopid} ({stop.name}) on Sqlite3 DB")
            else:
                # Stop currently saved but don't update it
                log.info(f"Stop ID #{stop.stopid} ({stop.name}) already saved on Sqlite3 DB, will not be updated")
                return
            cursor = self.db.cursor()
            cursor.execute(query, variables)
            self.db.commit()
            cursor.close()
        except sqlite3.DatabaseError as ex:
            log.error(f"Error saving the Stop ID #{stop.stopid} on Sqlite3 DB:\n{traceback.format_exc()}")
            raise StopSetterUnavailable(f"Error saving the stop on Sqlite database:\n{ex}")

    def get_all_saved_stops(self) -> List[int]:
        """Get the Stop IDs of all the Stops saved on this database
        :return: List with all the Stop IDs of the Stops saved on the database, as int
        :rtype: List[int]
        :raise: StopGetterUnavailable
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(_GET_ALL_STOP_IDS)
            output = cursor.fetchall()
            cursor.close()
        except sqlite3.DatabaseError as ex:
            log.error(f"Error getting all saved Stops on the Sqlite3 DB:\n{traceback.format_exc()}")
            raise StopGetterUnavailable(f"Error on Sqlite database:\n{ex}")
        else:
            log.info(f"Get All Saved Stops: Found {len(output)} Stops on the database")
            return [x[0] for x in output]

    def delete_stop(self, stopid: int) -> bool:
        """Delete a saved stop from the Sqlite DB, and return if the stop was deleted or not.
        :param stopid: ID of the Stop to delete
        :type stopid: int
        :return: True if stop was deleted, False if stop was not deleted (most probably because it was not saved)
        :rtype: bool
        :raise: StopDeleterUnavailable
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(_DELETE_STOP, (stopid,))
            count = cursor.rowcount
            cursor.close()
            if count:
                self.db.commit()
            deleted = bool(count)
        except sqlite3.DatabaseError as ex:
            log.error(f"Error deleting Stop ID #{stopid} from Sqlite3 DB:\n{traceback.format_exc()}")
            raise StopDeleterUnavailable(f"Error deleting the stop from Sqlite database:\n{ex}")
        else:
            # <log
            msg = f"Deleting the Stop ID #{stopid} from the Sqlite3 DB: "
            if deleted:
                msg += "Deleted successfully"
            else:
                msg += "Not deleted with no errors, maybe it was not saved on DB?"
            log.info(msg)
            # log>
            return deleted
