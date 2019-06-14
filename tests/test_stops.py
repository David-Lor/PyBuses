
# Native libraries
import sys
import logging
import unittest

# PyBuses modules
from pybuses import *

# Testing modules
from tests.helpers import log_method
from tests.dummy_assets import *

STOP_IDS = [1, 200, 300, 5800, 20700]
STOP_NAMES = ["My Testing Stop 1", "My Testing Stop 2", "My Testing Stop 3", "My Testing Stop 4"]
STOP_LOCATIONS = [41.393939, 21.414141, 81.1231232, 91.29381, 62.12321, 47.123123]

# Full logging
base_logger = logging.getLogger("pybuses")
log = logging.getLogger("pybuses.tests")


class TestStops(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(name)s (%(levelname)s) %(message)s"))
        base_logger.addHandler(handler)
        # Add "log_method" decorator programatically to all "test_" methods
        for test_str in [c for c in dir(cls) if callable(getattr(cls, c)) and c.startswith("test_")]:
            test_func = getattr(cls, test_str)
            setattr(cls, test_str, log_method(test_func, log))

    def test_stop_single_setter_offline_getter(self):
        """Test that a single Stop Setter and Offline Getter are working properly
        """
        # Simulate one single Source
        source = GenericSource()
        pybuses = PyBuses()
        pybuses.add_stop_setter(source.stop_setter)
        pybuses.add_stop_getter(source.offline_stop_getter, False)
        # Create a Stop and add to the setter
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0],
            lat=STOP_LOCATIONS[0],
            lon=STOP_LOCATIONS[1]
        )
        pybuses.save_stop(stop)
        # Find that stop with PyBuses
        pybuses_stop = pybuses.find_stop(STOP_IDS[0])
        # assertEqual
        log.info("Asserting the saved Stop attributes against the Stop found by PyBuses")
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        self.assertEqual(STOP_LOCATIONS[0], pybuses_stop.lat)
        self.assertEqual(STOP_LOCATIONS[1], pybuses_stop.lon)
        # assertRaises
        log.info("Asserting PyBuses returns StopNotFound searching for an unsaved stop having an Offline Getter")
        with self.assertRaises(StopNotFound):
            pybuses.find_stop(STOP_IDS[1])

    def test_stop_not_exist(self):
        """Test that searching a Stop having Online and Offline getters reports Stop Not Existing, instead of Not Found
        """
        # Simulate one single Source
        source = GenericSource()
        pybuses = PyBuses()
        pybuses.add_stop_getter(source.offline_stop_getter, False)
        pybuses.add_stop_getter(source.online_stop_getter, True)
        # <log
        log.info(
            "Online Getter and Offline Getter added to PyBuses, without Stops. "
            "When calling pybuses.find_stop, StopNotExist/StopNotFound should be raised."
        )
        # log>
        # assertRaises
        # <log
        log.info(
            "Calling pybuses.find_stop using default getter options; "
            "since Offline and Online Getters are used, StopNotExist exception "
            "will be raised by the Online Getter"
        )
        # log>
        with self.assertRaises(StopNotExist):
            pybuses.find_stop(STOP_IDS[0], auto_save=False)
        # assertRaises searching only with Offline getters
        # <log
        log.info(
            "Calling pybuses.find_stop using online=False to use Offline Getters only; "
            "since only the defined Offline Getter is used, StopNotFound exception "
            "will be raised by the Offline Getter"
        )
        # log>
        with self.assertRaises(StopNotFound):
            pybuses.find_stop(STOP_IDS[0], online=False, auto_save=False)

    def test_stop_online_offline_setter_getter(self):
        """Search for a stop having a Offline and Online Getters, and being the stop not available on the Offline Getter
        """
        # Simulate two different Sources (Offline and Online)
        source_online = GenericSource()
        source_offline = GenericSource()
        pybuses = PyBuses()
        pybuses.add_stop_getter(source_offline.offline_stop_getter, False)
        pybuses.add_stop_getter(source_online.online_stop_getter, True)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[1],
            name=STOP_NAMES[1],
            lat=STOP_LOCATIONS[2],
            lon=STOP_LOCATIONS[3]
        )
        source_online.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses
        pybuses_stop = pybuses.find_stop(STOP_IDS[1])
        # assertEqual
        log.info("Asserting the saved Stop attributes against the Stop found by PyBuses")
        self.assertEqual(STOP_IDS[1], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[1], pybuses_stop.name)
        self.assertEqual(STOP_LOCATIONS[2], pybuses_stop.lat)
        self.assertEqual(STOP_LOCATIONS[3], pybuses_stop.lon)
        # assertRaises
        # <log
        log.info(
            "Asserting that PyBuses raises StopNotExist searching for a Stop not existing on any of the sources, "
            "having an Online Getter that raises StopNotExist when queried for that stop"
        )
        # log>
        with self.assertRaises(StopNotExist):
            pybuses.find_stop(STOP_IDS[0])

    def test_stop_online_offline_setter_getter_with_autosave(self):
        """Search for a stop having Offline and Online Getters, being the stop not available on the Offline Getter,
        and having autosave=True on PyBuses instance. The Stop does not have location, which should be None
        """
        # Simulate two different Sources (Offline and Online)
        source_online = GenericSource()
        source_offline = GenericSource()
        # Initialize PyBuses with the global auto_save_stop=True
        pybuses = PyBuses(auto_save_stop=True)
        # Add the Offline and Online getters, and the setter of the Offline source
        pybuses.add_stop_getter(source_offline.offline_stop_getter, False)
        pybuses.add_stop_getter(source_online.online_stop_getter, True)
        pybuses.add_stop_setter(source_offline.stop_setter)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0]
        )
        source_online.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses, but only with Offline getters,
        # which should only search it through the Offline source getter,
        # raising StopNotFound since it does not exist on the Offline source
        # <log
        log.info(
            "Asserting that PyBuses raises StopNotFound searching for that stop when calling pybuses.find_stop with "
            "online=False, having the Offline Getter without that Stop saved, raising StopNotFound when queried for it"
        )
        # log>
        with self.assertRaises(StopNotFound):
            pybuses.find_stop(STOP_IDS[0], online=False)
        # Find that stop with PyBuses (using all the getters).
        # Since the Stop does not exist on the Offline source, it should be auto-saved on it
        pybuses_stop = pybuses.find_stop(STOP_IDS[0])
        # assertEqual (Stop returned by Online getter)
        log.info("Asserting the saved Stop attributes against the Stop found by PyBuses")
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        self.assertIsNone(pybuses_stop.lat)
        self.assertIsNone(pybuses_stop.lon)
        # Find that stop directly with the Offline source
        offline_stop = source_offline.offline_stop_getter(STOP_IDS[0])
        # assertEqual (Stop returned by Offline getter)
        self.assertEqual(STOP_IDS[0], offline_stop.stopid)
        self.assertEqual(STOP_NAMES[0], offline_stop.name)
        self.assertIsNone(offline_stop.lat)
        self.assertIsNone(offline_stop.lon)

    def test_stop_online_offline_setter_getter_without_autosave(self):
        """Search for a stop having a Offline and Online Getters, being the stop not available on the Offline Getter,
        and having autosave=False on PyBuses instance
        """
        # Simulate two different Sources (Offline and Online)
        source_online = GenericSource()
        source_offline = GenericSource()
        # Initialize PyBuses with the global auto_save_stop=True
        # but when searching the stop, the auto_save function will be disabled during that call
        pybuses = PyBuses(auto_save_stop=True)
        # Add the Offline and Online getters, and the setter of the Offline source
        pybuses.add_stop_getter(source_offline.offline_stop_getter, False)
        pybuses.add_stop_getter(source_online.online_stop_getter, True)
        pybuses.add_stop_setter(source_offline.stop_setter)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0]
        )
        source_online.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses, but only with Offline getters,
        # which should only search it through the Offline source getter,
        # raising StopNotFound since it does not exist on the Offline source
        # <log
        log.info(
            "Asserting that PyBuses raises StopNotFound searching for that stop when calling pybuses.find_stop with "
            "online=False, having the Offline Getter without that Stop saved, raising StopNotFound when queried for it"
        )
        # log>
        with self.assertRaises(StopNotFound):
            pybuses.find_stop(STOP_IDS[0], online=False)
        # Find that stop with PyBuses (using all the getters) and the parameter auto_save=False defined here,
        # not globally. Since the parameter is False, the Stop should not be saved on the Setter
        # when not located on the Offline getter
        pybuses_stop = pybuses.find_stop(STOP_IDS[0], auto_save=False)
        # assertEqual (Stop returned by Online getter)
        log.info("Asserting the saved Stop attributes against the Stop found by PyBuses")
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        # Find that stop with PyBuses, but only with Offline getters,
        # which should only search it through the Offline source getter
        with self.assertRaises(StopNotFound):
            pybuses.find_stop(STOP_IDS[0], online=False)

    def test_autosave_no_setters(self):
        """Search for a Stop having autosave=True on PyBuses instance and no Stop Setters defined.
        No exception should be raised
        """
        # Simulate one single Source
        source = GenericSource()
        pybuses = PyBuses(auto_save_stop=True)
        pybuses.add_stop_getter(source.online_stop_getter, online=True)
        # Create a Stop and save it directly on source
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0]
        )
        source.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses
        # <log
        log.info(
            "Going to call pybuses.find_stop, having auto_save_stop=True on PyBuses instance, but no setters defined; "
            "PyBuses will try to save the Stop, but since they are no Stop Setters defined, it cannot be done; "
            "however, no exceptions should be raised"
        )
        # log>
        pybuses_stop = pybuses.find_stop(STOP_IDS[0])
        # assertEqual (Stop returned by PyBuses)
        log.info("Asserting the saved Stop attributes against the Stop found by PyBuses")
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        # No exceptions should be raised

    def test_autosave_multiple_setters_save_on_all(self):
        """Search for a Stop having two Stop Setters defined, autosave=True and use_all_stop_setters=True on PyBuses.
        The stop should be auto-saved on the 2 Setters defined
        """
        # Simulate 3 sources (to use 2 Getters and 2 Setters)
        # Source 1: Offline Getter, 1st Setter
        # Source 2: Online Getter, No Setter
        # Source 3: No Getter, 2nd Setter
        source_1 = GenericSource()
        source_2 = GenericSource()
        source_3 = GenericSource()
        pybuses = PyBuses(auto_save_stop=True, use_all_stop_setters=True)
        # Add the Online getter first
        # PyBuses should query the offline getter first
        pybuses.add_stop_getter(source_2.online_stop_getter, online=True)
        pybuses.add_stop_getter(source_1.offline_stop_getter, online=False)
        pybuses.add_stop_setter(source_1.stop_setter)
        pybuses.add_stop_setter(source_3.stop_setter)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0],
            lat=STOP_LOCATIONS[0],
            lon=STOP_LOCATIONS[1]
        )
        source_2.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses
        # <log
        log.info(
            "Going to call pybuses.find_stop, having auto_save_stop=True and use_all_stop_setters=True on PyBuses "
            "instance; the Stop should be saved on all of them"
        )
        # log>
        pybuses_stop = pybuses.find_stop(STOP_IDS[0])
        # The Stop should be auto-saved on source_1 and source_3
        # Find that stop directly on source_1 and source_3
        stop_1 = source_1.stop_getter(STOP_IDS[0], False)
        stop_3 = source_1.stop_getter(STOP_IDS[0], False)
        # <log
        log.info(
            "Here are the Stop auto-saved by PyBuses on both defined setters:\n"
            "    Stop from 1st Setter: " + str(stop_1) + "\n"
            "    Stop from 2nd Setter: " + str(stop_3)
        )
        # log>
        # assertEqual
        # <log
        log.info(
            "Asserting the saved Stop attributes against the Stop found by PyBuses, and the Stops "
            "auto-saved by PyBuses on the two Setters defined"
        )
        # log>
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_IDS[0], stop_1.stopid)
        self.assertEqual(STOP_IDS[0], stop_3.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        self.assertEqual(STOP_NAMES[0], stop_1.name)
        self.assertEqual(STOP_NAMES[0], stop_3.name)
        self.assertEqual(STOP_LOCATIONS[0], pybuses_stop.lat)
        self.assertEqual(STOP_LOCATIONS[0], stop_1.lat)
        self.assertEqual(STOP_LOCATIONS[0], stop_3.lat)
        self.assertEqual(STOP_LOCATIONS[1], pybuses_stop.lon)
        self.assertEqual(STOP_LOCATIONS[1], stop_1.lon)
        self.assertEqual(STOP_LOCATIONS[1], stop_3.lon)

    def test_autosave_multiple_setters_save_on_first(self):
        """Search for a Stop having two Stop Setters defined, autosave=True and use_all_stop_setters=False (default)
        on PyBuses. The stop should be auto-saved only on the first Setter
        """
        # Simulate 3 sources (to use 2 Getters and 2 Setters)
        # Source 1: Offline Getter, 1st Setter
        # Source 2: Online Getter, No Setter
        # Source 3: No Getter, 2nd Setter
        source_1 = GenericSource()
        source_2 = GenericSource()
        source_3 = GenericSource()
        pybuses = PyBuses(auto_save_stop=True)
        # Add the Online getter first
        # PyBuses should query the offline getter first
        pybuses.add_stop_getter(source_2.online_stop_getter, online=True)
        pybuses.add_stop_getter(source_1.offline_stop_getter, online=False)
        pybuses.add_stop_setter(source_1.stop_setter)
        pybuses.add_stop_setter(source_3.stop_setter)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[0],
            name=STOP_NAMES[0],
            lat=STOP_LOCATIONS[0],
            lon=STOP_LOCATIONS[1]
        )
        source_2.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses
        # <log
        log.info(
            "Going to call pybuses.find_stop, having auto_save_stop=True but use_all_stop_setters=False (as default) "
            "on PyBuses instance; the Stop should be saved only on the first Stop Setter"
        )
        # log>
        pybuses_stop = pybuses.find_stop(STOP_IDS[0])
        # The Stop should be auto-saved on source_1 but not on source_3
        # assertRaises when directly searching that stop on source_3
        log.info("Asserting that the Stop is Not Found on the 2nd Stop Setter defined")
        with self.assertRaises(StopNotFound):
            source_3.stop_getter(STOP_IDS[0], False)
        # Find that stop directly on source_1
        stop_1 = source_1.stop_getter(STOP_IDS[0], False)
        log.info("The Stop exists on the 1st Stop Setter defined:\n    " + str(stop_1))
        # assertEqual
        # <log
        log.info(
            "Asserting the saved Stop attributes against the Stop found by PyBuses, and the Stop "
            "auto-saved by PyBuses on the first Setter defined"
        )
        # log>
        self.assertEqual(STOP_IDS[0], pybuses_stop.stopid)
        self.assertEqual(STOP_IDS[0], stop_1.stopid)
        self.assertEqual(STOP_NAMES[0], pybuses_stop.name)
        self.assertEqual(STOP_NAMES[0], stop_1.name)
        self.assertEqual(STOP_LOCATIONS[0], pybuses_stop.lat)
        self.assertEqual(STOP_LOCATIONS[0], stop_1.lat)
        self.assertEqual(STOP_LOCATIONS[1], pybuses_stop.lon)
        self.assertEqual(STOP_LOCATIONS[1], stop_1.lon)

    def test_autosave_stop_setter_unavailable(self):
        """Search for a Stop having three Stop Setters defined, the first of them always raising StopSetterUnavailable;
        autosave=True and use_all_stop_setters=False (default) on PyBuses,
        so the stop should be saved on the second getter."""
        # Simulate 3 sources (to use 1 Getter and 3 Setters)
        # Source 1: Offline Getter, 1st Setter (always raise StopSetterUnavailable)
        # Source 2: 2nd Setter
        # Source 3: 3rd Setter
        # Source 4: Online Getter
        source_1 = GenericSource()
        source_2 = GenericSource()
        source_3 = GenericSource()
        source_4 = GenericSource()
        pybuses = PyBuses(auto_save_stop=True)
        # Add the Online getter first
        # PyBuses should query the offline getter first
        pybuses.add_stop_getter(source_1.offline_stop_getter, online=False)
        pybuses.add_stop_getter(source_4.online_stop_getter, online=True)
        pybuses.add_stop_setter(source_1.broken_stop_setter)
        pybuses.add_stop_setter(source_2.stop_setter)
        pybuses.add_stop_setter(source_3.stop_setter)
        # Create a Stop and save it directly on Online source
        stop = Stop(
            stopid=STOP_IDS[1],
            name=STOP_NAMES[1],
            lat=STOP_LOCATIONS[2],
            lon=STOP_LOCATIONS[3]
        )
        source_4.stop_setter(stop, False)
        log.info("Saved a new Stop on the Online source")
        # Find that stop with PyBuses
        # <log
        log.info(
            "Going to call pybuses.find_stop, having auto_save_stop=True but use_all_stop_setters=False (as default) "
            "on PyBuses instance, and being the first defined Stop Setter unavailable (always failing), so the Stop "
            "should be saved on the next available Setter, which is the second one"
        )
        # log>
        pybuses_stop = pybuses.find_stop(STOP_IDS[1])
        # The Stop should be auto-saved on source_2 but not on source_1 nor source_3
        # assertRaises when directly searching that stop on source_1 and source_3
        log.info("Asserting that the Stop is Not Found on the 1st (always failing) and 3rd Stop Setters defined")
        with self.assertRaises(StopNotFound):
            source_1.stop_getter(STOP_IDS[1], False)
        with self.assertRaises(StopNotFound):
            source_3.stop_getter(STOP_IDS[1], False)
        # Find that stop directly on source_2
        stop_2 = source_2.stop_getter(STOP_IDS[1], False)
        log.info("The Stop exists on the 2nd Stop Setter defined:\n    " + str(stop_2))
        # assertEqual
        # <log
        log.info(
            "Asserting the saved Stop attributes against the Stop found by PyBuses, and the Stop "
            "auto-saved by PyBuses on the second Setter defined"
        )
        # log>
        self.assertEqual(STOP_IDS[1], pybuses_stop.stopid)
        self.assertEqual(STOP_NAMES[1], pybuses_stop.name)
        self.assertEqual(STOP_LOCATIONS[2], pybuses_stop.lat)
        self.assertEqual(STOP_LOCATIONS[3], pybuses_stop.lon)
        self.assertEqual(STOP_IDS[1], stop_2.stopid)
        self.assertEqual(STOP_NAMES[1], stop_2.name)
        self.assertEqual(STOP_LOCATIONS[2], stop_2.lat)
        self.assertEqual(STOP_LOCATIONS[3], stop_2.lon)
