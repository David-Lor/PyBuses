
# Native modules
import logging
from typing import Optional, List, Callable
from collections import namedtuple, OrderedDict

# Package modules
from .helpers import update_all_stops_from_getters, debug_functions, function_to_str, UpdateAllStopsFromGettersReturn
from .exceptions import *
from .assets import *

__all__ = ["PyBuses", "BusSortMethods", "logger"]

logger = logging.getLogger("pybuses.core")
log = logger


"""Bus Sorting Methods are ints, but must be used with the aliases from the BusSortMethods Named Tuple.
NONE = 0
TIME = 1
LINE = 2
ROUTE = 3
LINE_INT = 4
MIXED_LINE_ROUTE = 5
MIXED_LINE_INT_ROUTE = 6
"""
_bus_sort_methods_namedtuple = namedtuple("BusSortMethods", ["NONE", "TIME", "LINE", "ROUTE"])
BusSortMethods = _bus_sort_methods_namedtuple(0, 1, 2, 3)


class PyBuses(object):
    """A PyBuses object to help managing bus stops and look for incoming buses.
    This object should be threated as a concrete transport service, i.e.:
        - "the bus service of King's Landing"
        - "the metro service of Liberty City"
        - "the train service of Hamburg"
        - "the bus service of Hamburg"
    Each one of these services would have a PyBuses object, with their getters, setters and deleters.

    Getters are custom, required functions that fetch Stop info and Bus lists from certain sources.
    At least one Stop Getter and one Bus Getter are required to fetch stops and buses respectively.

    Setters are custom, optional functions, that will save found Stops or list of buses to custom destinations
    (i.e. a database, local variables, a file, cache...).
    Setters are supposed to be executed after a Stop or Bus query is successful, but this behaviour can be customized.

    Deleters are custom, optional functions, that will delete saved Stops or list of buses on custom destinations,
    usually the same places as Setters.

    The PyBuses methods that use these functions are:
        - Stop Getters: find_stop()
        - Stop Setters: save_stop()
        - Stop Deleters: delete_stop()
        - Bus Getters: get_buses()
        - Bus Setters: save_buses()
        - Bus Deleters: delete_buses()
    Bus Setters and Bus Deleters functionality is not implemented yet.

    Please refer to documentation in order to check how Getter, Setter and Deleter functions must work.
    """

    def __init__(
            self,
            use_all_stop_setters: bool = False,
            use_all_bus_setters: bool = False,
            use_all_stop_deleters: bool = True,
            use_all_bus_deleters: bool = True,
            auto_save_stop: bool = False
    ):
        """
        :param use_all_stop_setters: if True, use all the defined Stop Setters when saving a Stop (default=False)
        :param use_all_bus_setters: if True, use all the defined Bus Setters when saving a Bus (default=False)
        :param use_all_stop_deleters: if True, use all the defined Stop Deleters when deleting a Stop (default=True)
        :param use_all_bus_deleters: if True, use all the defined Bus Deleters when deleting a Bus (default=True)
        :param auto_save_stop: if True, when searching a Stop through an Online getter,
                               save it on the Setter/s automatically (default=False)
        :type use_all_stop_setters: bool
        :type use_all_bus_setters: bool
        :type use_all_stop_deleters: bool
        :type use_all_bus_deleters: bool
        """
        self.stop_getters: OrderedDict[Callable, bool] = OrderedDict()  # { StopGetter : online(True/False) }
        self.stop_setters: List[Callable] = list()
        self.stop_deleters: List[Callable] = list()
        self.bus_getters: List[Callable] = list()
        self.bus_setters: List[Callable] = list()
        self.bus_deleters: List[Callable] = list()
        self.use_all_stop_setters: bool = use_all_stop_setters
        self.use_all_bus_setters: bool = use_all_bus_setters
        self.use_all_stop_deleters: bool = use_all_stop_deleters
        self.use_all_bus_deleters: bool = use_all_bus_deleters
        self.auto_save_stop: bool = auto_save_stop

        # <log
        log.debug(
            "Initialized a new PyBuses instance with the following configuration:\n"
            f" * {len(self.stop_getters)} Stop Getters defined: {debug_functions(self.stop_getters)}\n"
            f" * {len(self.stop_setters)} Stop Setters defined: {debug_functions(self.stop_setters)}\n"
            f" * {len(self.stop_deleters)} Stop Deleters defined: {debug_functions(self.stop_deleters)}\n"
            f" * {len(self.bus_getters)} Bus Getters defined: {debug_functions(self.bus_getters)}\n"
            f" * {len(self.bus_setters)} Bus Setters defined: {debug_functions(self.bus_setters)}\n"
            f" * {len(self.bus_deleters)} Bus Deleters defined: {debug_functions(self.bus_deleters)}\n"
            f" * Using all Stop Setters: {self.use_all_stop_setters}\n"
            f" * Using all Bus Setters: {self.use_all_bus_setters}\n"
            f" * Using all Stop Deleters: {self.use_all_stop_deleters}\n"
            f" * Using all Bus Deleters: {self.use_all_bus_deleters}\n"
            f" * Auto Save Stops: {self.auto_save_stop}\n"
        )
        # log>

    def find_stop(self, stopid: int, online: Optional[bool] = None, auto_save: Optional[bool] = None) -> Stop:
        """Find a Stop using the defined Stop Getters on this PyBuses instances.
        If no Stop Getters are defined, MissingGetters exception is raised.
        'online' parameter define if using Online or Offline getters, or all of them (using Offline getters first)
        :param stopid: ID of the Stop to find
        :param online: if True, only search on Online Stop Getters |
                       if False, only search on Offline Stop Getters |
                       if None, search on all Stop Getters, but search on Offline Getters first (default=None)
        :param auto_save: if True and the Stop was fetched by an Online getter, save it using the 'save_stop' method |
                          if False, do nothing about it |
                          if None, use default value on this PyBuses instance (default=None) |
                          Exceptions produced by the Stop Setters will be ignored and not raised;
                          Additional parameters of the 'save_stop' method will be used as defaulted
        :type stopid: int
        :type online: bool or None
        :type auto_save: bool
        :return: Stop object
        :rtype: list of Stop or False or Exception
        :raise: MissingGetters if no getters are defined |
                StopNotFound if the stop could not be found by any of the getters, and all the getters worked fine |
                StopNotExist if a getter raised this exception (the getter is sure that the stop does not exist) |
                StopGetterUnavailable if the stop could not be fetched from any getter, no getter raised StopNotExist,
                and at least one getter raised StopGetterUnavailable
        """
        getters: List[Callable] = self.get_stop_getters(online=online, sort=True, online_first=False)
        if auto_save is None:
            # Get instance auto_save parameter if not defined on this method call
            auto_save = self.auto_save_stop

        if not getters:
            msg = "No Stop getters defined on this PyBuses instance"
            log.warning(msg)
            raise MissingGetters(msg)
        else:
            # <log
            log.debug(
                f"Searching Stop ID #{stopid} having {len(getters)} getters available"
                f" ({'Online only' if online else ('Offline only' if online == False else 'Online & Offline')}, "
                f"{'Auto-Saving' if auto_save else 'Not Auto-Saving'})"
            )
            # log>

        errors = False  # set to True if any getter raised StopGetterUnavailable
        for getter in getters:  # type: Callable
            try:
                stop = getter(stopid)

            # If the Getter raises StopNotExist exception, it will not be catched here
            # because it is confirmed by a trusted getter that the stop does not exist
            # and that exception must be catched by the caller to know that situation

            except StopNotFound:
                log.debug(f"Stop ID #{stopid} not found using the Getter {function_to_str(getter)}")
                continue

            except StopNotExist as ex:
                log.debug(f"Stop ID #{stopid} reported as not existing by the Getter {function_to_str(getter)}")
                raise ex
                # raise StopNotExist from ex

            except StopGetterUnavailable as ex:
                # <log
                log.warning(
                    f"Stop ID #{stopid} could not be found using the getter {function_to_str(getter)}"
                    "\n{ex}" if str(ex) else ""
                )
                # log>
                errors = True
                continue

            else:  # Stop found
                # <log
                log.debug(
                    f"Stop ID#{stopid} found using the Getter {function_to_str(getter)}!\n"
                    f"Stop Name: {stop.name}\n"
                    f"Stop Location: {stop.lat}, {stop.lon}"
                    f"\nStop additional info: {stop.other}" if stop.other else ""
                )
                # log>

                if auto_save and getter in self.get_stop_getters(online=True):
                    # Auto-Save stop if required and was found by an Online getter
                    log.debug(f"Stop ID #{stopid} must be saved on the Stop Setter/s available")
                    # TODO This should run threaded to avoid blocking the return while saving the Stop
                    try:
                        self.save_stop(stop)
                    except SetterException:
                        pass  # QUESTION add log here? or just log on save_stop method?

                return stop

        if errors:
            # Stop not found, and Errors on one or more getters
            msg = "Stop info{} could not be retrieved for any of the Stop getters available"
            log.warning(msg.format(f" for StopID #{stopid}"))
            raise StopGetterUnavailable(msg.format(""))

        else:
            # Stop not found, but No errors on the getters
            msg = "Stop{} not found by any of the Stop getters available"
            log.info(msg.format(f" ID #{stopid}"))
            raise StopNotFound(msg.format(""))

    def save_stop(self, stop: Stop, update: bool = True, use_all_stop_setters: Optional[bool] = None):
        """Save the provided Stop object on the Stop setters defined.
        The stop will only be saved on the first Setter where the Stop is saved successfully,
        unless 'use_all_stop_setters' attribute of PyBuses class or on this method is True.
        If no Stop Setters are defined, MissingSetters exception is raised.
        If none of the Stop setters worked, StopSetterUnavailable exception is raised.
        If the stop is saved on at least one Stop Setter, the Stop is considered successfully saved.
        :param stop: Stop object to save
        :param update: if True, when the Stop currently exists on a Setter data destination,
                       update/overwrite stop on destination with the current data of the Stop provided (default=True)
        :param use_all_stop_setters: if True, save the Stop on all the Stop Setters |
                                     if False, save the Stop on the first Stop Setter where it is saved successfully |
                                     if None, use the value declared on this PyBuses instance (default=None)
        :type stop: Stop
        :type update: bool
        :type use_all_stop_setters: bool or None
        :raise: MissingSetters | StopSetterUnavailable
        """
        setters: List[Callable] = self.get_stop_setters()
        if use_all_stop_setters is None:
            # Get instance use_all_stop_setters parameter if not defined on this method call
            use_all_stop_setters = self.use_all_stop_setters

        if not setters:
            msg = "No Stop setters defined on this PyBuses instance"
            log.warning(msg)
            raise MissingSetters(msg)
        else:
            # <log
            log.debug(
                f"Saving Stop ID #{stop.stopid} having {len(setters)} setters available"
                f" ({'Update: YES' if update else 'Update: NO'}, "
                f"""use_all_stop_setters={
                    'Using all Stop Setters' if use_all_stop_setters else 'Using only the first successful Stop Setter'
                })"""
            )
            # log>

        success = False  # Variable to know if the Stop was successfully saved on at least one Stop Setter
        for setter in setters:  # type: Callable
            try:
                setter(stop, update=update)

            except StopSetterUnavailable as ex:
                # <log
                log.warning(
                    f"Stop ID #{stop.stopid} ({stop.name}) "
                    f"could not be saved using the setter {function_to_str(setter)}"
                    f"\n{ex}" if str(ex) else ""
                )
                # log>

                continue

            else:
                success = True
                log.info(f"Stop ID #{stop.stopid} ({stop.name}) saved successfully "
                         f"using the setter {function_to_str(setter)}")
                if not use_all_stop_setters:
                    break

        if not success:
            msg = "Stop{} could not be saved on any of the Stop setters defined"
            log.warning(msg.format(f" ID #{stop.stopid} ({stop.name}"))
            raise StopSetterUnavailable(msg.format(""))

    def delete_stop(self, stopid: int, use_all_stop_deleters: Optional[bool] = None):
        """Delete the stop that matches the given Stop ID using the defined Stop Deleters.
        The stop will only be deleted on the first Deleter where the Stop was deleted successfully,
        unless use_all_stop_deleters attribute of PyBuses class is True (which is by default).
        No exceptions will be raised if the stop was not deleted because it was not registered.
        Only when all the Deleters themselves failed, StopDeleterUnavailable will be raised.
        If no Stop Deleters are defined, MissingDeleters exception is raised.
        :param stopid: Stop ID of the Stop to delete
        :param use_all_stop_deleters: if True, delete the Stop using all the Stop Deleters
               (default=use the value declared on this PyBuses instance)
        :type stopid: int
        :type use_all_stop_deleters: bool
        :raise: MissingDeleters | StopDeleterUnavailable
        """
        deleters: List[Callable] = self.get_stop_deleters()

        if not deleters:
            raise MissingDeleters("No Stop deleters defined on this PyBuses instance")
        else:
            log.debug(f"Removing Stop ID #{stopid} having {len(deleters)} deleters available")

        success = False  # Variable to know at the end if the stop was successfully deleted with at least one deleter
        if use_all_stop_deleters is None:
            # Get instance use_all_stop_setters parameter if not defined on this method call
            use_all_stop_deleters = self.use_all_stop_deleters

        for deleter in deleters:  # type: Callable
            try:
                deleter(stopid)
            except StopDeleterUnavailable:
                log.warning(f"Stop ID #{stopid} could not be removed using the deleter {function_to_str(deleter)}")
                continue
            else:
                success = True
                if not use_all_stop_deleters:
                    break

        if not success:
            raise StopDeleterUnavailable("Stop could not be deleted with any of the Stop deleters defined")

    def update_all_stops_from_getters(
            self,
            end: int,
            start: int = 1,
            threads: int = 0,
            update: bool = True,
            use_all_stop_setters: Optional[bool] = None
    ) -> UpdateAllStopsFromGettersReturn:
        """Find all the stops when the online resources do not provide a full list of Stops.
        This method will manually search the Stops by ID sequentially
        between the 'start' and 'end' ranges of Stop IDs using the available Online Stop Getters.
        The method can run on the background using threads.
        The 'threads' parameter define how many threads will be used. By default is 0, which means use no threads.
        All the threads start on the method, and a list with all these created Threads is returned.
        All the found stops will be saved/updated using the Stop setters defined on the PyBuses instance.
        If no Stop Getters are defined, MissingGetters exception is raised.
        If no Stop Setters are defined, MissingSetters exception is raised.
        :param end: Stop ID limit to search
        :param start: First Stop ID to search (default=1)
        :param threads: number of threads to use (default=0: use no threads)
        :param update: if True, when a found Stop currently exists on a Setter data destination,
                       update stop on destination with the current data of the Stop provided (default=True)
        :param use_all_stop_setters: if True, try to save each Stop on each one of the available Stop Setters
                                     (default=None: use the value declared on this PyBuses instance)
        :type end: int
        :type start: int
        :type threads: int
        :type update: bool
        :type use_all_stop_setters: bool or None
        :raise: MissingGetters or MissingSetters
        :return: The Namedtuple 'UpdateAllStopsFromGettersReturn' from helpers, which contains:
             1.- 'created_threads': List of created threads (if no threads are used, empty list)
             2.- 'error_stops': List with the Stop IDs of Stops that could not be fetched from any of the Getters
             3.- 'non_saved_stops': List with the Stop IDs of Stops that could not be saved on any of the Setters
             4.- 'threads_stop_event': Stop Event to stop all the threads created
        :rtype: UpdateAllStopsFromGettersReturn
        When using threads, the lists will be returned empty, but can be filled with stop IDs during threads execution.
        """
        getters: List[Callable] = self.get_stop_getters(online=True)  # Get all Online getters
        if not getters:
            msg = "No Stop getters defined on this PyBuses instance, so cannot perform Update all stops from getters"
            log.warning(msg)
            raise MissingGetters(msg)
        if not self.get_stop_setters():
            msg = "No Stop setters defined on this PyBuses instance, so cannot perform Update all stops from getters"
            log.warning(msg)
            raise MissingSetters(msg)
        return update_all_stops_from_getters(
            pybuses=self,
            use_all_stop_setters=use_all_stop_setters,
            start=start,
            end=end,
            update=update,
            threads=threads
        )

    def get_buses(self, stopid: int, sort_by: Optional[int] = BusSortMethods.TIME, reverse: bool = False) -> List[Bus]:
        """Get a live list of all the Buses coming to a certain Stop and the remaining time until arrival.
        The bus list can be sorted using the 'sort_by' and one of the methods available on 'BusSortMethods'.
        By default, buses list is sorted by Time, from shorter time (first to arrive) to greater time (last to arrive).
        If no Bus Getters are defined, MissingGetters exception is raised.
        :param stopid: ID of the Stop to get the list of the incoming buses of
        :param sort_by: method used to sort buses; use constants available in 'BusSortMethods' (default=TIME).
                        If None, the buses list will not be sorted.
        :param reverse: if True, reverse sort the buses (default=False)
        :type stopid: int
        :type sort_by: int or None
        :type reverse: bool
        :return: List of Buses
        :rtype: List[Bus]
        :raise: MissingGetters or StopNotExist or StopNotFound or BusGetterUnavailable
        """
        getters: List[Callable] = self.get_bus_getters()

        if not getters:
            msg = "No Bus getters defined on this PyBuses instance"
            log.warning(msg)
            raise MissingGetters(msg)
        else:
            # <log
            log.debug(
                f"Getting Buses for Stop ID #{stopid} having {len(getters)} getters available, "
                f"sort by {BusSortMethods._fields[list(BusSortMethods).index(sort_by)]} {'Reversed' if reverse else ''}"
                if sort_by is not None else "no sort"
            )
            # log>

        for getter in getters:  # type: Callable
            try:
                buses: List[Bus] = getter(stopid)
                if sort_by == BusSortMethods.TIME:
                    buses.sort(key=lambda x: x.time, reverse=reverse)
                elif sort_by == BusSortMethods.LINE:
                    buses.sort(key=lambda x: x.line, reverse=reverse)
                elif sort_by == BusSortMethods.ROUTE:
                    buses.sort(key=lambda x: x.route, reverse=reverse)
                # <log
                msg = f"Found {len(buses)} buses coming to the Stop ID #{stopid}"
                if buses:
                    for bus in buses:
                        msg += f"\n{bus.line} ({bus.route}) - Time: {bus.time}"
                log.debug(msg)
                # log>
                return buses

            except BusGetterUnavailable:
                # <log
                log.warning(
                    f"Buses for Stop ID #{stopid} could not be fetched "
                    f"using the getter {function_to_str(getter)}"
                )
                # log>
                continue

        msg = "Bus list{} could not be retrieved with any of the Bus getters defined"
        log.warning(msg.format(f"for Stop ID #{stopid}"))
        raise BusGetterUnavailable(msg.format(""))

    def save_buses(self):
        """Mock function that would save a list of buses to a local storage. Not implemented.
        :return:
        """
        pass

    def delete_buses(self):
        """Mock function that would delete a list of buses from a local storage. Not implemented.
        :return:
        """
        pass

    def add_stop_getter(self, getter, online: bool = False):
        """Add one Stop Getter to this PyBuses instance.
        It should be known if the Stop Getter is connected to a Online or a Offline source,
        and set the 'online' arg to True/False depending on it.
        :param getter: one or more StopGetter functions/methods
        :param online: boolean to define if the Getter is connected or not to a Online source (default=False)
        :type getter: StopGetter
        :type online: bool
        """
        self.add_stop_getters(getter, online=online)

    def add_stop_getters(self, *args, **kwargs):
        """Add multiple Stop Getters to this PyBuses instance.
        It should be known if the Stop Getters are connected to a Online or a Offline source,
        and set the 'online' kwarg to True/False depending on it.
        Online and Offline Getters should not be mixed on a single call to this method.
        :param args: one or more StopGetter functions/methods
        :param kwargs: online=True/False (if no value = False)
        """
        online = kwargs.get("online", False)
        for f in args:  # type: Callable
            self.stop_getters[f] = bool(online)
        # <log
        log.debug(
            f"Added {len(args)} new {'Online' if online else 'Offline'} Stop Getter. "
            f"Current list of Stop Getters:\n{debug_functions(self.stop_getters)}"
        )
        # log>

    def add_stop_setter(self, f: Callable):
        """Add one Stop Setter to this PyBuses instance.
        :param f: one Stop Setter function/method
        :type f: function or class method
        """
        self.stop_setters.append(f)
        log.debug(
            f"Added a new Stop Setter. Current list of Stop Setters:\n"
            f"{debug_functions(self.stop_setters)}"
        )

    def add_stop_deleter(self, f: Callable):
        """Add one Stop Deleter to this PyBuses instance.
        :param f: one Stop Deleter function/method
        :type f: function or class method
        """
        self.stop_deleters.append(f)
        log.debug(
            f"Added a new Stop Deleter. Current list of Stop Deleters:\n"
            f"{debug_functions(self.stop_deleters)}"
        )

    def add_bus_getter(self, f: Callable):
        """Add one Bus Getter to this PyBuses instance.
        :param f: one Bus Getter function/method
        :type f: function or class method
        """
        self.bus_getters.append(f)
        log.debug(
            f"Added a new Bus Getter. Current list of Bus Getters:\n"
            f"{debug_functions(self.bus_getters)}"
        )

    def add_bus_setter(self, f: Callable):
        """Add one Bus Setter to this PyBuses instance.
        :param f: one Bus Setter function/method
        :type f: function or class method
        """
        self.bus_setters.append(f)
        log.debug(
            f"Added a new Bus Setter. Current list of Bus Setters:\n"
            f"{debug_functions(self.bus_setters)}"
        )

    def add_bus_deleter(self, f: Callable):
        """Add one Bus Deleter to this PyBuses instance.
        :param f: one Bus Deleter function/method
        :type f: function or class method
        """
        self.bus_deleters.append(f)
        log.debug(
            f"Added a new Bus Deleter. Current list of Bus Deleters:\n"
            f"{debug_functions(self.bus_deleters)}"
        )

    def get_stop_getters(
            self, online: Optional[bool] = None,
            sort: bool = True, online_first: bool = False
    ) -> List[Callable]:
        """Get all the Stop Getters available on this PyBuses instance.
        The 'online' parameter can be specified to get only Online or Offline getters,
        otherwise all available getters will be returned.
        :param online: if True, get only getters connected to a Online source |
                       if False, get only getters connected to a Offline source |
                       if None, get both Online and Offline getters (default=None)
        :param sort: when getting both Online and Offline getters,
                     return them sorted by the Online getters first, then Offline getters, or vice versa,
                     depending on the 'online_first' parameter (default=True)
        :param online_first: when sorting the getters, if True, sort by the Online getters first, then Offline getters;
                             if False, sort by the Offline getters first, then Online getters (default=False)
        :type online: bool | None
        :type sort: bool
        :type online_first: bool
        :return: list of available Stop Getters
        :rtype: List[Callable]
        """
        if online is None:
            getters = list(self.stop_getters.keys())
            if sort:
                return sorted(getters, key=lambda k: self.stop_getters[k], reverse=online_first)  # TODO Test sorted
            else:
                return getters
        else:
            return [g for g in self.stop_getters.keys() if self.stop_getters[g] == bool(online)]

    def get_stop_setters(self) -> List[Callable]:
        """Get all the Stop Setters available on this PyBuses instance.
        :return: list of available Stop Setters
        :rtype: List[Callable]
        """
        return self.stop_setters

    def get_stop_deleters(self) -> List[Callable]:
        """Get all the Stop Deleters available on this PyBuses instance.
        :return: list of available Stop Deleters
        :rtype: List[Callable]
        """
        return self.stop_deleters

    def get_bus_getters(self) -> List[Callable]:
        """Get all the Bus Getters available on this PyBuses instance.
        :return: list of available Bus Getters
        """
        return self.bus_getters

    def get_bus_setters(self) -> List[Callable]:
        """Get all the Bus Setters available on this PyBuses instance.
        :return: list of available Bus Setters
        :rtype: List[Callable]
        """
        return self.bus_setters

    def get_bus_deleters(self) -> List[Callable]:
        """Get all the Bus Deleters available on this PyBuses instance.
        :return: list of available Bus Deleters
        :rtype: List[Callable]
        """
        return self.bus_deleters
