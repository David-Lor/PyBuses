
"""This module keeps a local cache of stops saved in a dict.
Each StopsCache object is a cache of Stops objects,
used by each instance of PyBuses.
This should be the first Stop Getter on the PyBuses objects.
"""

#Native libraries
import threading
import atexit
from datetime import datetime
from time import sleep
#Own modules
from .Assets import Stop
from .Logger import cache_log as log

class StopsCache(object):
    def __init__(self):
        self.stops = {} #Format: {Stop : datetime}
        self._cleanup_service_stopEvent = threading.Event()
        self._cleanup_service_thread = None
        log.debug("Created a new Stops Cache")
        @atexit.register
        def atexit_f():
            log.debug("Closing Stops Cache")
            self.stop_cleanup_service()

    def find_stop_cache(self, stopid):
        """Search a stop in local stops cache (list).
        :param stopid: StopID of the stop to search on cache
        :return: Stop object if stop is found
        :return: None if stop is not found
        """
        log.debug("Searching Stop #{} in local cache".format(stopid))
        try:
            stop = next(stop for stop in tuple(self.stops.keys()) if stop.id == int(stopid))
            log.debug("Stop #{} found in local cache (Name={})".format(stopid, stop.name))
            return stop
        except StopIteration:
            log.debug("Stop #{} not found in local cache".format(stopid))
            return None #Can't return False, because stop not registered in cache doesn't mean the stop doesn't exist

    def save_stop_cache(self, stop):
        """Store a stop in local stops cache (list).
        If a Stop object with the same StopID is on the list, won't be added.
        :param stop: Stop object to save on local cache
        """
        if not self.find_stop_cache(stopid=stop.id):
            self.stops[stop] = datetime.now()
            log.debug("Stop #{} stored in local cache".format(stop.id))
        else:
            log.debug("Tried to store Stop #{} in local cache, but was already there".format(stop.id))

    def _cleanup_service(self, age, stopEvent):
        timeout = age/2
        log.debug("Starting Cleanup Service with age={}".format(age))
        while not stopEvent.is_set():
            now = datetime.now()
            log.debug("Checking for expired stops stored in local cache for cleanup")
            for stop in list(self.stops): #Check each stored Stop
                try:
                    stop_datetime = self.stops[stop] #Get datetime when stop was stored
                    if (now-stop_datetime).seconds >= age: #If stop expired
                        self.stops.pop(stop) #Remove from local cache
                        log.debug("Stop #{} expired and removed from local cache".format(stop.id))
                except RuntimeError:
                    log.debug("RuntimeError trying to check Stop #{} in local cache".format(stop.id))
                    pass
            stopEvent.wait(timeout=timeout)

    def start_cleanup_service(self, age=1800):
        """Start the Cached Stops Cleanup Service as a thread.
        The thread will remove cached stops older than "age".
        :param age: limit the time (seconds) a stop will stay in the cache
        """
        self._cleanup_service_stopEvent.clear()
        self._cleanup_service_thread = threading.Thread(
            target=self._cleanup_service,
            args=(age, self._cleanup_service_stopEvent),
            daemon=True
        )
        self._cleanup_service_thread.start()
        log.debug("Local cache Cleanup Service started")

    def stop_cleanup_service(self):
        """Stop the Cached Stops Cleanup Service thread,
        if exists and is running
        """
        if self.is_cleanup_service_running():
            self._cleanup_service_stopEvent.set()
            log.debug("Local cache Cleanup Service stopped")
        else:
            log.debug("Local cache Cleanup Service asked to stop, but was already stopped")

    def is_cleanup_service_running(self):
        """Get the Cached Stops Cleanup Service thread status.
        :return: True if thread is running
        :return: False if thread is stopped or not initialized
        """
        if self._cleanup_service_thread is None:
            return False
        return self._cleanup_service_thread.is_alive()
