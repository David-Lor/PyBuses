
# Native libraries
import atexit
import logging
import traceback
from typing import Union, Optional, List

# Installed libraries
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

# Package modules
from .assets import Stop
from .helpers import current_timestamp
from .exceptions import *


logger = logging.getLogger("pybuses.mongodb")
log = logger


"""STRUCTURE OF MongoDB DATABASE used by PyBuses
The database only helds Stop data, including Google Maps & StreetView related data

Database: pybuses
Collection: stops

Structure of documents (fields with * are optional, so they can be missing on certain stops)
{
    "_id": 1234,
    "name": "123 Fake St.",
    "saved": <dt>,
    "updated": <dt>,
    "other" : {dict}
    "lat": 1.23456, *
    "lon": -1.23456 *
}
```
Stop ID is used as the Document ID of MongoDB.
<dt> are ints with the timestamp when Stop was saved for first time and updated for last time.
Other is a dict with optional extra data declared on PyBuses Stop objects. Is always present although is empty.
* these fields are optional, so some entries might not have them.
Timestamps are saved on Unix/Epoch format, and UTC timezone.
"""
# http://api.mongodb.com/python/current/tutorial.html

__all__ = [
    "MongoDB", "DEFAULT_TIMEOUT", "DEFAULT_DATABASE_NAME", "DEFAULT_DATABASE_COLLECTION",
    "PyMongoError", "MongoDBUnavailable"
]

DEFAULT_TIMEOUT = 1
DEFAULT_DATABASE_NAME = "pybuses"
DEFAULT_DATABASE_COLLECTION = "stops"


class MongoDB(object):
    """This MongoDB object is part of the PyBuses framework, and interacts with a MongoDB database server
    to save and fetch the required data from it, like Stops and Buses.
    """

    # noinspection PyTypeChecker
    def __init__(
            self,
            host: str = "localhost",
            port: int = 27017,
            uri: Optional[str] = None,
            timeout: Union[int, float] = DEFAULT_TIMEOUT,
            db_name: str = DEFAULT_DATABASE_NAME,
            stops_collection_name: str = DEFAULT_DATABASE_COLLECTION
    ):
        """Location of the server must be given using host and port parameters, or uri.
        If URI is provided, host and port parameters will be ignored.
        A connection with the database will be performed automatically, if possible.
        Otherwise, connect method must be called after declaring correct server info (host+port/URI).
        :param host: Host where MongoDB server is hosted (default="localhost")
        :param port: Port of the MongoDB server (default=27017)
        :param uri: URI of the server, instead of host and port (default=None)
        :param timeout: Timeout for MongoDB operations in seconds (default=10)
        :param db_name: Name of the database used by PyBuses (default="pybuses")
        :param stops_collection_name: Name of the db collection used for the stops
        :type host: str
        :type port: int
        :type uri: str or None
        :type timeout: int or float
        :type db_name: str
        :type stops_collection_name: str
        """
        self.timeout: Union[int, float] = timeout
        self.host: str = host
        self.port: int = port
        self.uri: Optional[str] = uri
        self.db_name: str = db_name
        self.stops_collection_name: str = stops_collection_name
        self.client: MongoClient = None
        self.db: Database = None
        self.collection: Collection = None
        self.documents: Collection = None

        # Try to connect DB on init
        try:
            self.connect()
        except PyMongoError:
            log.error(f"Could not auto-connect to MongoDB during initialization:\n{traceback.format_exc()}")
            self.close()

        # Register the close method atexit
        atexit.register(self.close)

        # Alias
        self.disconnect = self.close
        self.is_connected = self.check_connection
        self.is_initialized = self.check_client
        self.remove_stop = self.delete_stop
        self.documents = self.collection

    def connect(self, timeout: Optional[Union[int, float]] = None):
        """Connect to the MongoDB database. MongoClient instance is saved on self.client.
        :param timeout: Timeout for the connect operation. If not set, timeout declared on MongoDB instance will be used
        :type timeout: int or float or None
        :raise: PyMongoError
        """
        if timeout is None:
            timeout = self.timeout
        if self.uri is None:
            self.client = MongoClient(
                host=self.host,
                port=self.port,
                serverSelectionTimeoutMS=int(timeout * 1000)
            )
        else:
            self.client = MongoClient(
                uri=self.uri,
                serverSelectionTimeoutMS=int(timeout * 1000)
            )
        self.db = self.client[self.db_name]
        self.collection = self.db[self.stops_collection_name]
        # <log
        log.info(
            f"MongoDB connected at "
            f"{self.host}:{self.port}" if self.uri is None else self.uri
        )
        # log>

    def close(self):
        """Disconnect the MongoDB database.
        If database was already closed, nothing will happen.
        """
        if self.check_client():
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
            self.documents = None
            log.info("MongoDB disconnected")

    def check_client(self, raise_exception: bool = False) -> bool:
        """Check if the client object is initialized.
        A initialized client does not mean that is connected with the MongoDB server: use check_connection to check it.
        :param raise_exception: Raise MongoDBUnavailable exception if client not initialized (default=False)
        :return: True if client initialized, False if not
        :rtype: bool
        :raise: MongoDBUnavailable if raise_exception=True and the MongoDB client is not initialized
        """
        is_client = isinstance(self.client, MongoClient)
        if raise_exception and not is_client:
            raise MongoDBUnavailable("Client of MongoDB on this instance has not been initialized yet")
        return is_client

    def check_connection(self, raise_exception: bool = False) -> bool:
        """Tries to perform a operation on the database, and returns True if it was successful.
        Otherwise, if raise_exception=False, returns True.
        If raise_exception=True, the related PyMongo exception will be raised and must be catched on origin.
        :param raise_exception: if True, don't catch exceptions in this method (default=False)
        :type raise_exception: bool
        :return: True if connection is OK; False if connection is down or could not perform the operation
        :rtype: bool
        :raise: PyMongoError if raise_exception=True
        """
        def _f():
            self.client.admin.command("ismaster")
        if not self.check_client():
            return False
        if raise_exception:
            _f()
        else:
            try:
                _f()
            except PyMongoError:
                return False
            else:
                return True

    def find_stop(self, stopid: int) -> Stop:
        """Search a Stop on MongoDB database by the StopID.
        This method is used as a StopGetter function of PyBuses.
        :param stopid: ID of the Stop to search
        :type stopid: int
        :return: found Stop object
        :rtype: Stop
        :raise: StopNotFound or StopGetterUnavailable
        """
        try:
            self.check_client(True)
            result = self.documents.find_one({"_id": stopid})
        except PyMongoError as ex:
            log.error(f"Error while searching Stop ID #{stopid} on MongoDB:\n{traceback.format_exc()}")
            raise StopGetterUnavailable(f"Error while searching Stop on MongoDB:\n{ex}")
        if isinstance(result, dict):
            log.info(f"Stop ID #{stopid} found! Returned JSON:\n{result}")
            return dict_to_stop(result)
        else:
            log.info(f"Stop ID #{stopid} not found on this MongoDB database")
            raise StopNotFound(f"Stop not found on MongoDB database")

    def is_stop_saved(self, stopid: int) -> bool:
        """Check if the given Stop is saved on the database.
        :param stopid: ID of the Stop to search
        :type stopid: int
        :return: True if Stop is saved, False if not found on database
        :rtype: bool
        :raise: StopGetterUnavailable
        """
        try:
            self.check_client(True)
            result = bool(self.documents.find_one({"_id": stopid}))
            log.debug(f"Checked if Stop ID #{stopid} is saved on MongoDB: Result: {result}")
            return result
        except PyMongoError as ex:
            raise StopGetterUnavailable(f"Error checking if the stop is saved:\n{ex}")

    def get_all_saved_stops(self) -> List[int]:
        """Get the Stop IDs of all the Stops saved on this database
        :return: List with all the Stop IDs of the Stops saved on the database, as int
        :rtype: List[int]
        :raise: StopGetterUnavailable
        """
        try:
            self.check_client(True)
            stops = [x for x in self.documents.distinct("_id")]
            log.info(f"Get All Saved Stops: Found {len(stops)} Stops on the database")
            return stops
        except PyMongoError as ex:
            log.error(f"Error getting all saved Stops on this MongoDB:\n{traceback.format_exc()}")
            raise StopGetterUnavailable(f"Error while getting all the Stop IDs saved on this MongoDB database:\n{ex}")

    def save_stop(self, stop: Stop, update: bool = True):
        """Save or update a Stop on this MongoDB.
        If update=True and the stop is currently saved, it will be updated with the Stop provided.
        This method is used as a StopSetter function of PyBuses.
        :param stop: The Stop to save, with all the available information completed (at least ID and Name are required)
        :param update: if True, when the Stop to save exists in database, update it with the Stop provided
        :type stop: Stop
        :type update: bool
        :raise: StopSetterUnavailable
        """
        try:
            self.check_client(True)
            exists = self.is_stop_saved(stop.stopid)
            if not exists:
                # Stop not currently saved on DB, and save it
                d = dict(stop)
                stopid = d.pop("stopid")
                d["_id"] = stopid
                curtime = current_timestamp()
                d["saved"] = curtime
                d["updated"] = curtime
                self.documents.insert_one(d)
                log.info(f"Saved Stop ID #{stop.stopid} ({stop.name}) on MongoDB")
            elif update:
                # Stop currently saved, and update it
                d = dict(stop)
                d.pop("stopid")
                d["updated"] = current_timestamp()
                self.documents.update_one(
                    filter={"_id": stop.stopid},
                    update={"$set": d}
                )
                log.info(f"Updated Stop ID #{stop.stopid} ({stop.name}) on MongoDB")
            else:
                # Stop currently saved but don't update it
                log.info(f"Stop ID #{stop.stopid} ({stop.name}) currently saved on MongoDB, will not be updated")
        except PyMongoError as ex:
            log.error(f"Error saving the Stop ID #{stop.stopid} on MongoDB:\n{traceback.format_exc()}")
            raise StopSetterUnavailable(f"Error while saving Stop to MongoDB:\n{ex}")

    def delete_stop(self, stopid: int) -> bool:
        """Delete a saved stop from MongoDB, and return if the stop was deleted or it did not exist in database.
        :param stopid: ID of the Stop to delete
        :type stopid: int
        :return: True if stop was deleted, False if stop was not deleted (most probably because it was not saved)
        :rtype: bool
        :raise: StopDeleterUnavailable
        """
        try:
            self.check_client(True)
            deleted = bool(self.collection.delete_one({"_id": stopid}).deleted_count)
        except PyMongoError as ex:
            log.error(f"Error deleting Stop ID #{stopid} from MongoDB:\n{traceback.format_exc()}")
            raise StopDeleterUnavailable(f"Error while deleting Stop from MongoDB:\n{ex}")
        else:
            # <log
            msg = f"Deleting the Stop ID #{stopid} from MongoDB: "
            if deleted:
                msg += "Deleted successfully"
            else:
                msg += "Not deleted with no errors, maybe it was not saved on DB?"
            log.info(msg)
            # log>
            return deleted


def dict_to_stop(dictionary: dict) -> Stop:
    """Convert a dictionary with Stop info, returned by MongoDB, to a Stop object.
    This is a helper used when reading a Stop from MongoDB, since it returns dictionaries.
    The dictionary must have valid Stop info, with at least "_id" and "name" keys.
    :param dictionary: Dictionary given by a Stop query on MongoDB
    :type dictionary: dict
    :return: Stop object
    :rtype: Stop
    """
    stop = Stop(
        stopid=dictionary["_id"],
        name=dictionary["name"]
    )
    if "lat" in dictionary.keys():
        stop.lat = dictionary["lat"]
    if "lon" in dictionary.keys():
        stop.lon = dictionary["lon"]
    if "other" in dictionary.keys():
        stop.other = dictionary["other"]
    stop.other["saved"] = dictionary["saved"]
    stop.other["updated"] = dictionary["updated"]
    return stop
