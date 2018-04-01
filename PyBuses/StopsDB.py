
#Own modules
from .Assets import Stop
from .Logger import db_log as log


class StopsDatabase(object):
    def __init__(self, db):
        """
        :param db: Database object
        """
        self.db = db
        self.db.write("""CREATE TABLE IF NOT EXISTS stops(
            stopid UNSIGNED INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            lat TEXT,
            lon TEXT,
            registered TEXT,
            updated TEXT
        )""")
        log.info("Started Stops SQLite Database ({})".format(db.db_filename))

    def find_stop(self, stopid):
        """Search a stop saved in local database.
        :param stopid: Stop ID to find (int)
        :return: Stop object with all the available info filled, it stop is found
        :return: None if stop is not found
        """
        log.debug("Searching Stop #{} in DB".format(stopid))
        out = self.db.read("SELECT * FROM stops WHERE stopid = ?", (stopid,), fetchall=False)
        if out is None: #Stop not found
            log.debug("Stop #{} not found in DB".format(stopid))
            return None #Can't return False, because stop not registered in DB doesn't mean the stop doesn't exist.
        log.debug("Stop #{} found in DB".format(stopid))
        return Stop( #Stop found
            stopid=out[0],
            name=out[1],
            lat=out[2],
            lon=out[3]
        )

    def save_stop(self, stop, update=False):
        """Save a stop to database, or update data of a saved stop.
        :param stop: Created Stop object (with all the available info filled)
        :param update: if True, update stop info when it's already registered in DB
        """
        try:
            exists = bool(self.db.read(
                "SELECT COUNT(stopid) FROM stops WHERE stopid = ?",
                (stop.id,),
                fetchall=False,
                single_column=True
            ))
            if update and exists:
                self.db.write("""UPDATE stops SET
                    name = ?,
                    lat = ?,
                    lon = ?,
                    updated = ?
                """, (stop.name, stop.lat, stop.lon, self.db.curdate()))
                log.info("Updated Stop #{} in DB (Name={})".format(stop.id, stop.name))
            elif not exists:
                dt = self.db.curdate()
                self.db.write("INSERT INTO stops VALUES (?,?,?,?,?,?)", (stop.id, stop.name, stop.lat, stop.lon, dt, dt))
                log.info("Saved Stop #{} ({}) in DB".format(stop.id, stop.name))
            else:
                log.debug("Asked to save Stop #{} in DB, but it already exists".format(stop.id))
        except Exception:
            log.exception("Error {action} Stop #{stopid} in DB".format(
                action="updating" if update else "saving",
                stopid=stop.id
            ))
