
#Own modules
from Databases import Database
from .StopsDB import StopsDatabase
from .StopsCache import StopsCache
from .GoogleStreetView import GoogleStreetView
from .GoogleMaps import GoogleMaps
from .Logger import init_log as log


class PyBuses(object):
    """A PyBuses object that will help organizing bus stops and lookup incoming buses.
    Object must be initialized with a list of Stop and Bus getter functions,
    which must interact with the online server that provides Stop info and Buses.
    """
    
    def __init__(self, stop_getters, bus_getters, db_name="Databases/Stops.sqlite"):
        """A PyBuses object, associated with a city/bus service using stop and bus getters.
        :param stop_getters: a single or list of functions to get info of a stop
        :param bus_getters: a single or list of functions to get buses coming to a stop
        :param db_name: name (relative route) of SQLite database where Stop info will be stored
        """
        #Create cache and database for stops
        self.stops_cache = StopsCache()
        self.db = Database(db_name)
        self.stopsdb = StopsDatabase(self.db)
        
        #Set Stop getters
        self._native_stop_getters = (self.stops_cache.find_stop_cache, self.stopsdb.find_stop)
        self.stop_getters = list(self._native_stop_getters)
        if type(stop_getters) not in (list, tuple):
            stop_getters = (stop_getters,)
        self.stop_getters.extend(stop_getters) #Add custom getters to stop getters list
        
        #Set Bus getters
        self.bus_getters = []
        if type(bus_getters) not in (list, tuple):
            bus_getters = (bus_getters,)
        self.bus_getters.extend(bus_getters)
        
        #Stops Cache - start cleanup service (thread)
        self.stops_cache.start_cleanup_service(age=215)
        
        #Google StreetView/Maps objects
        self.streetview = GoogleStreetView(self.db)
        self.maps = GoogleMaps(self.db)
        
        #Debug everything:
        # log.info("Created a PyBuses stops with the getters from {module}:\n* Stop getters: {stopgg}\n* Bus getters: {busgg}".format(
        #     stopgg=str(tuple(f.__name__ for f in self.stop_getters)),
        #     busgg=str(tuple(f.__name__ for f in self.bus_getters))
        # ))
        logmsg = "Created a PyBuses stops with the following getters:"
        for getter in (self.stop_getters + self.bus_getters):
            logmsg += "\n[{type}] {name} from {module}".format(
                type="Stop" if getter in self.stop_getters else "Bus",
                name=getter.__name__,
                module=getter.__module__
            )
        log.debug(logmsg)

    class StopNotFound(Exception):
        """This will be raised when a stop isn't found from find_stop methods
        (which means a Stop getter replied that stop doesn't exist)
        """
        pass

    def find_stop(self, stopid):
        log.info("Searching for Stop #{}".format(stopid))
        for getter in self.stop_getters:
            log.debug("Searching Stop #{stopid} with getter {getter}@{gmodule}".format(
                stopid=stopid,
                getter=getter.__name__,
                gmodule=getter.__module__
            ))
            result = getter(stopid=stopid)
            if result and result.name is not None: #Stop found
                log.info("Stop #{stopid} (Name={stopname}) found by getter {getter}@{gmodule}".format(
                    stopid=stopid,
                    stopname=result.name,
                    getter=getter.__name__,
                    gmodule=getter.__module__
                ))
                if getter not in self._native_stop_getters or getter != self.stops_cache.find_stop_cache:
                    log.info("Saving Stop #{} in local cache".format(stopid))
                    self.save_stop_cache(result) #Save stop in local cache if it wasn't cached
                elif getter not in self._native_stop_getters:
                    log.info("Saving Stop #{} in DB".format(stopid))
                    self.save_stop_db(result) #Save stop in DB if it wasn't in DB
                return result
            if result is False: #Stop not found
                log.debug("Stop #{} identified as Not Found/Unexistent".format(stopid))
                raise self.StopNotFound("Stop {} not found!".format(stopid))
            #If error (result is None): keep trying other getters
        #Raise error if couldn't retrieve Stop info from any of the getters
        log.warning("Could not retrieve Stop #{} info from any of the getters available; none reported it as non-existant".format(stopid))
        raise ConnectionError("Could not retrieve Stop #{} info from any of the getters".format(stopid))

    def get_buses(self, stopid):
        log.info("Getting buses for Stop #{}".format(stopid))
        for getter in self.bus_getters:
            result = getter(stopid=stopid)
            if type(result) is list:
                result.sort(key = lambda x: x.time) #Sort buses by time
                log.info("Found {nbuses} buses for Stop #{stopid} with the getter {getter}@{gmodule}".format(
                    nbuses=len(result),
                    stopid=stopid,
                    getter=getter.__name__,
                    gmodule=getter.__module__
                ))
                return result
            #If error: keep trying other getters
        #Raise error if couldn't retrieve Bus list from any of the getters
        log.warning("Could not retrieve buses for Stop #{} from any of the getters available".format(stopid))
        raise ConnectionError("Could not retrieve buses for Stop #{} from any of the getters".format(stopid))

    def save_stop_db(self, stop):
        self.stopsdb.save_stop(stop)

    def update_stop_db(self, stop):
        self.stopsdb.save_stop(stop, update=True)
    
    def save_stop_cache(self, stop):
        self.stops_cache.save_stop_cache(stop)

    def get_streetview(self, stop):
        return self.streetview.get_streetview(stop)
