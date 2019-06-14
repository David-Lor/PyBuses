
# Native libraries
import logging
import json
from time import time
from collections import OrderedDict, namedtuple
from typing import List, Tuple, Dict, Union, Optional
from threading import Thread, Lock, Event

# Package modules
from .exceptions import *


logger = logging.getLogger("pybuses.helpers")
log = logger

UpdateAllStopsFromGettersReturn = namedtuple(
    "UpdateAllStopsFromGettersReturn",
    ["created_threads", "error_stops", "non_saved_stops", "threads_stop_event"]
)


def update_all_stops_from_getters(
        pybuses,
        start: int,
        end: int,
        threads: int,
        use_all_stop_setters: bool,
        update: bool
) -> UpdateAllStopsFromGettersReturn:
    """Search all Stops sequentially from 'start' to 'end' IDs.
    Is and must be called from the same named method of PyBuses.
    :param pybuses: PyBuses object (instance)
    :param start: Stop ID to Start from
    :param end: Stop ID to End on
    :param threads: Threads to use (0=use no threads)
    :param use_all_stop_setters: if True, save found stops on all Stop Setters |
                                 if False, save on the first successful Stop Setter
    :param update: if True, update Stops saved on data destinations if are already registered |
                   if False, do not save on the destination if already registered
    :return: A tuple with three lists:
             1.- List of created threads (if no threads are used, empty list)
             2.- List with the Stop IDs of Stops that could not be fetched from any of the Getters
             3.- List with the Stop IDs of Stops that could not be saved on any of the Setters
    :rtype: UpdateAllStopsFromGettersReturn (namedtuple[List[Thread], List[int], List[int], Event])
    When using threads, the lists will be returned empty, but will be filled with stop IDs during threads execution.
    """
    created_threads: List[Thread] = list()
    error_stops: List[int] = list()
    non_saved_stops: List[int] = list()
    threads_stop_event = Event()

    def _report_stop_errors():
        if len(error_stops) > 0:
            log.warning(f"{len(error_stops)} Stops could not be searched from any of the getters: {error_stops}")
        if len(non_saved_stops) > 0:
            log.warning(f"{len(error_stops)} Stops could not be saved on any of the setters: {non_saved_stops}")

    def _find_stop_and_save(stopid_tofind):  # Function used by threads/no-thread
        try:
            log.info(f"Searching Stop {stopid_tofind}")
            stop = pybuses.find_stop(stopid=stopid_tofind, online=True, auto_save=False)
        except StopGetterUnavailable as ex:
            msg = f"Error searching stop {stopid_tofind} from the getters"
            if str(ex):
                msg += f"\n{ex}"
            log.info(msg)
            error_stops.append(stopid_tofind)
        except (StopNotFound, StopNotExist):
            log.info(f"Stop {stopid_tofind} reported as not found by online getter")
        else:
            try:
                log.info(f"Stop {stop.stopid} found! Name={stop.name}, lat={stop.lat}, lon={stop.lon}")
                pybuses.save_stop(stop, update=update, use_all_stop_setters=use_all_stop_setters)
            except StopSetterUnavailable as ex:
                msg = f"Stop {stop.stopid} ({stop.name}) could not be saved on the Setters"
                if str(ex):
                    msg += f"\n{ex}"
                log.warning(msg)
                non_saved_stops.append(stop.stopid)

    if threads <= 0:  # Use no threads
        log.debug("Scanning available Stops using the Update All Stops From Getters tool, using no threads")
        for stopid in range(start, end + 1):
            _find_stop_and_save(stopid)
        _report_stop_errors()

    else:  # Use threads
        log.debug(f"Scanning available Stops using the Update All Stops From Getters tool, using {threads} threads")

        class Counter(object):
            def __init__(self, initial, limit):
                self.value: int = initial
                self.limit: int = limit
                self.lock = Lock()

            def get(self):
                self.lock.acquire()
                current = self.value
                if current > self.limit:
                    self.lock.release()
                    raise IndexError()
                self.value += 1
                self.lock.release()
                return current

        counter = Counter(initial=start, limit=end)

        def _thread_f(th_counter: Counter, stop_event: Event):  # Function for threads
            while not stop_event.is_set():
                try:
                    stopid_tofind = th_counter.get()
                except IndexError:
                    break
                else:
                    _find_stop_and_save(stopid_tofind)

        for i in range(threads):
            th = Thread(target=_thread_f, args=(counter, threads_stop_event))
            created_threads.append(th)
            th.start()

    # return created_threads, error_stops, non_saved_stops, threads_stop_event
    return UpdateAllStopsFromGettersReturn(
        created_threads=created_threads,
        error_stops=error_stops,
        non_saved_stops=non_saved_stops,
        threads_stop_event=threads_stop_event
    )


def current_timestamp() -> int:
    """Return current datetime in Unix/Epoch format and UTC timezone.
    :return: current Unix/Epoch timestamp in UTC timezone, parsed to int
    :rtype: int
    """
    return int(time())

#####################################################
# MISC/RANDOM HELPERS
#####################################################


def migrate_stops(origin, destination) -> Tuple[List[int], List[int]]:
    """Copy all stops saved on a MongoDB database to a SQLite database.
    Database objects must be initialized beforehand.
    :param origin: instance of a data source that must have get_all_saved_stops and find_stop working methods
    :param destination: instance of a data source that must have save_stop working method
    :return: Tuple with two results: found StopIDs of Stops in MongoDB, and successfully saved stops in SQLite DB
    :rtype: List[int], List[int]
    :raise: StopGetterUnavailable
    """
    stops_ids = origin.get_all_saved_stops()
    success = list()
    for stopid in stops_ids:
        try:
            stop = origin.find_stop(stopid)
            destination.save_stop(stop)
        except StopException:
            pass
        else:
            success.append(stopid)
    return stops_ids, success


def str_to_json(json_str: str) -> Dict:
    """
    :param json_str:
    :return:
    """
    return json.loads(json_str.replace("'", '"'))


#####################################################
# LOGGING HELPERS
#####################################################


def function_to_str(function, online: Optional[bool] = None) -> str:
    """Convert a function/method to a string with the format "<name>@<module> (<online>)", for debug/logging purposes.
    Online parameter is only printed if the functions list is a Dict.
    :param function: function or method to be analyzed
    :param online: if the function is Online or Offline (if required) (Optional)
    :type function: function/method
    :type online: bool | None
    :return: formatted string
    :rtype: str
    """
    st = f"{function.__name__}@{function.__module__}"
    if online is not None:
        st += f" ({'Online' if online else 'Offline'})"
    return st


def debug_functions(functions: Union[Dict, OrderedDict, List]) -> List[str]:
    """Convert a dict or list of PyBuses getters/setters/deleters functions to strings, for debug/logging purposes.
    Format of each function string: "<name>@<module> (<online>)". A list of strings is returned.
    Online parameter is only printed if the functions list is a Dict.
    :param functions: dictionary of type {function: bool (Online/Offline) with the functions/methods used by PyBuses |
                      list of functions
    :type functions: dict | OrderedDict | list
    :return: list of formatted strings (one per each function/method)
    :rtype: List[str]
    """
    if isinstance(functions, dict):
        return [function_to_str(func, functions[func]) for func in functions.keys()]
    else:
        return [function_to_str(func) for func in functions]
