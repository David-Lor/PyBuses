
# Native libraries
import os
import sys
import unittest
import logging

# PyBuses modules
from pybuses import *

# Testing modules
from tests.dummy_assets import *
from tests.helpers import generate_stopid, log_method


CONFIG = {  # These settings can be replaced using ENV variables with the same names
    "TEST_MONGO_HOST": "127.0.0.1",
    "TEST_MONGO_PORT": 27017,
    "TEST_MONGO_DB": "pybuses_testing",
    "TEST_MONGO_CLEAR": True,
}

for key in CONFIG.keys():
    try:
        if key == "TEST_MONGO_CLEAR":
            try:
                CONFIG[key] = bool(int(os.environ[key]))
            except ValueError:
                pass
        else:
            CONFIG[key] = os.environ[key]
    except KeyError:
        pass

# Full logging
base_logger = logging.getLogger("pybuses")
log = logging.getLogger("pybuses.tests")


class TestMongoDB(unittest.TestCase):
    db: MongoDB = None
    saved_stops: List[int] = list()

    @classmethod
    def setUpClass(cls):
        cls.db = MongoDB(
            host=CONFIG["TEST_MONGO_HOST"],
            port=CONFIG["TEST_MONGO_PORT"],
            db_name=CONFIG["TEST_MONGO_DB"]
        )
        base_logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(name)s (%(levelname)s) %(message)s"))
        base_logger.addHandler(handler)
        # Add "log_method" decorator programatically to all "test_" methods
        for test_str in [c for c in dir(cls) if callable(getattr(cls, c)) and c.startswith("test_")]:
            test_func = getattr(cls, test_str)
            setattr(cls, test_str, log_method(test_func, log))

    @classmethod
    def tearDownClass(cls):
        if CONFIG["TEST_MONGO_CLEAR"]:
            log.info(f"{len(cls.saved_stops)} stops generated: {cls.saved_stops}")
            log.info("Removing these stops from MongoDB...")
            deleted_stops = list()
            not_deleted_stops = list()
            for stopid in cls.saved_stops:
                try:
                    if not cls.db.delete_stop(stopid):
                        raise IOError
                except (StopDeleterUnavailable, IOError):
                    not_deleted_stops.append(stopid)
                else:
                    deleted_stops.append(stopid)
            log.info(f"{len(deleted_stops)} stops deleted: {deleted_stops}")
            if not_deleted_stops:
                log.info(f"{len(not_deleted_stops)} stops NOT deleted: {not_deleted_stops}")
        else:
            log.warning("WARNING: Stops generated and saved on MongoDB WILL NOT BE CLEARED")
        cls.db.disconnect()

    def test_connection(self):
        """Check if the MongoDB connection is UP
        """
        self.assertTrue(self.db.check_connection(raise_exception=False))

    """STOPS
    IDs: from 1 to 100
    - Stops without Location, without Other: 1 to 20
    - Stops with Location, without Other: 21 to 50
    - Stops with Location, with Other: 51 to 70
    - Stops without Location, with Other: 71 to 100
    """

    def test_get_stop_auto_save(self):
        """Search a Stop that does not exist on MongoDB, but is available on an Online getter.
        Use the PyBuses auto_save option set to True. Check if the stop is saved after searching it.
        """
        # Initialize PyBuses with the getter and setter from Sqlite
        pybuses = PyBuses(auto_save_stop=True)
        pybuses.add_stop_setter(self.db.save_stop)
        pybuses.add_stop_getter(online_stop_getter, online=True)
        pybuses.add_stop_getter(self.db.find_stop, online=False)
        # Generate the Stop to work with
        stopid = generate_stopid(1, 100, self.saved_stops)
        stop_pybuses = pybuses.find_stop(stopid)
        # Stop should be saved on MongoDB
        saved = self.db.is_stop_saved(stopid)
        stop_mongo = self.db.find_stop(stopid)
        self.assertTrue(saved)
        self.assertEqual(stop_pybuses.stopid, stop_mongo.stopid)
        self.assertEqual(stop_pybuses.name, stop_mongo.name)

    def test_get_stop_no_auto_save(self):
        """Search a Stop that does not exist on MongoDB, but is available on an Online getter.
        Use the PyBuses auto_save option set to False. Check if the stop is saved after searching it.
        """
        # Initialize PyBuses with the getter and setter from Sqlite
        # auto_save feature is disabled on find_stop
        pybuses = PyBuses(auto_save_stop=True)
        pybuses.add_stop_setter(self.db.save_stop)
        pybuses.add_stop_getter(online_stop_getter, online=True)
        pybuses.add_stop_getter(self.db.find_stop, online=False)
        # Generate the Stop to work with
        stopid = generate_stopid(1, 100, self.saved_stops)
        pybuses.find_stop(stopid, auto_save=False)
        # Delete generated stop from the List, since it is not saved on DB
        self.saved_stops.remove(stopid)
        # Stop should not be saved on MongoDB
        saved = self.db.is_stop_saved(stopid)
        self.assertFalse(saved)

    def test_stop_save_is_saved(self):
        """Save a stop on DB and check if is saved, using the is_stop_saved method.
        """
        stopid = generate_stopid(1, 100, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Query DB if Stop is saved
        saved = self.db.is_stop_saved(stopid)
        self.assertTrue(saved)

    def test_stop_save_read_only_name(self):
        """Save a stop on DB, read it and check if the name of the stop read from DB matches the name of the stop saved.
        """
        stopid = generate_stopid(1, 20, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Assert attributes from saved and read Stop objects
        self.assertEqual(stop.stopid, stop_db.stopid)
        self.assertEqual(stop.name, stop_db.name)

    def test_stop_save_read_only_location(self):
        """Save a stop on DB, read it and check if the location of the stop read from DB matches the location
        of the stop saved.
        """
        stopid = generate_stopid(21, 50, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Assert attributes from saved and read Stop objects
        self.assertEqual(stop.stopid, stop_db.stopid)
        self.assertEqual(stop.name, stop_db.name)
        self.assertEqual(stop.lat, stop_db.lat)
        self.assertEqual(stop.lon, stop_db.lon)

    def test_stop_save_read_only_other(self):
        """Save a stop on DB, read it and check if the Other dict from the stop read from DB matches
        the Other dict of the stop saved.
        """
        stopid = generate_stopid(51, 70, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Remove saved and updated keys from stop_db Other dict
        stop_db.other.pop("saved")
        stop_db.other.pop("updated")
        # Assert attributes from saved and read Stop objects
        self.assertEqual(stop.stopid, stop_db.stopid)
        self.assertEqual(stop.name, stop_db.name)
        self.assertDictEqual(stop.other, stop_db.other)

    def test_search_stop_not_saved(self):
        """Search a Stop on the database that does not exist.
        The StopNotFound exception must be raised by the Stop getter method.
        """
        stopid = 8080
        self.assertRaises(StopNotFound, self.db.find_stop, stopid)  # (Exception, function, args)

    def test_stop_save_read_check_time(self):
        """Save a stop on DB, read the stop, get the Saved and Updated times on the Other dict,
        and the Saved and Updated times directly from the DB entry, then compare them.
        """
        stopid = generate_stopid(1, 20, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read Saved and Updated times directly from DB
        js = self.db.documents.find_one({"_id": stopid})
        saved = js["saved"]
        updated = js["updated"]
        # Read Stop object from DB
        stop_db = self.db.find_stop(stopid)
        # Get Saved and Updated values on Other dictionary
        other = stop_db.other
        saved_db = other.pop("saved")
        updated_db = other.pop("updated")
        # Check if saved and updated times match
        self.assertEqual(saved, saved_db)
        self.assertEqual(updated, updated_db)

    def test_stop_save_read_location_and_other(self):
        """Save a stop on DB, read it and check if the location and Other dict from the stop read from DB matches
        the location and Other dict of the stop saved.
        """
        stopid = generate_stopid(71, 100, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Remove saved and updated keys from stop_db Other dict
        stop_db.other.pop("saved")
        stop_db.other.pop("updated")
        # Assert attributes from saved and read Stop objects
        self.assertEqual(stop.stopid, stop_db.stopid)
        self.assertEqual(stop.name, stop_db.name)
        self.assertEqual(stop.lat, stop_db.lat)
        self.assertEqual(stop.lon, stop_db.lon)
        self.assertDictEqual(stop.other, stop_db.other)

    def test_stop_modify_name(self):
        """Save a stop on DB, modify it's name, save again (updating it), read from DB and compare
        if modified name matches the name of the stop on DB.
        """
        stopid = generate_stopid(71, 100, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Change Stop name
        random_number = random.randint(1, 1000)
        modified_name = stop.name + " Modified #" + str(random_number)
        stop.name = modified_name
        self.db.save_stop(stop, update=True)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Current name of Stop in DB must match the modified name
        self.assertEqual(modified_name, stop_db.name)

    def test_stop_modify_location(self):
        """Save a stop on DB, modify it's location, save again (updating it), read from DB and compare
        if modified location matches the location of the stop on DB.
        """
        stopid = generate_stopid(21, 50, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Change Stop location (current location * 0.5)
        lat = stop.lat
        lon = stop.lon
        new_lat = lat * 0.5
        new_lon = lon * 0.5
        stop.lat = new_lat
        stop.lon = new_lon
        self.db.save_stop(stop, update=True)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Current location must match saved coordinates
        self.assertAlmostEqual(new_lat, stop_db.lat)
        self.assertAlmostEqual(new_lon, stop_db.lon)

    def test_stop_modify_other(self):
        """Save a stop on DB, modify it's Other dict, save again (updating it), read from DB and compare
        if modified Other dict matches the Other dict of the stop on DB.
        """
        stopid = generate_stopid(51, 70, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Read from DB
        stop_db = self.db.find_stop(stopid)
        # Remove saved and updated keys from stop_db_2 Other dict
        stop_db.other.pop("saved")
        stop_db.other.pop("updated")
        # Add a new dict key
        stop_db.other["new_dict_item"] = "hello!"
        stop_dict_modified = stop_db.other
        # Update the stop
        self.db.save_stop(stop_db, update=True)
        # Read again from DB
        stop_db_2 = self.db.find_stop(stopid)
        # Remove saved and updated keys from stop_db_2 Other dict
        stop_db_2.other.pop("saved")
        stop_db_2.other.pop("updated")
        # Assert attributes from saved and 2nd read Stop objects
        self.assertEqual(stop.stopid, stop_db_2.stopid)
        self.assertEqual(stop.name, stop_db_2.name)
        self.assertDictEqual(stop_dict_modified, stop_db_2.other)

    def test_stop_save_already_saved_no_update(self):
        """Save a stop on DB, modify it's Other dict, save again (forcing to NOT update), read from DB and compare
        if modified Other dict does not match the Other dict of the stop on DB.
        """
        stopid = generate_stopid(21, 50, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        original_name = stop.name
        # Save on DB
        self.db.save_stop(stop)
        # Modify name
        new_name = original_name + " Modified!!!"
        # Request saving the stop with no update
        self.db.save_stop(stop, update=False)
        # Read stop from DB
        stop_db = self.db.find_stop(stopid)
        # Names must not match (stop from DB name must be the first name)
        self.assertNotEqual(new_name, stop_db.name)
        self.assertEqual(original_name, stop_db.name)

    def test_stop_delete(self):
        """Save a stop on DB, check if it is saved, then delete it and check if it is saved again.
        """
        stopid = generate_stopid(1, 100, self.saved_stops)
        # Generate the Stop to save
        stop = online_stop_getter(stopid)
        # Save on DB
        self.db.save_stop(stop)
        # Check that it was saved
        saved_first = self.db.is_stop_saved(stopid)
        # Delete from DB
        self.db.delete_stop(stopid)
        # Check that is not saved now
        saved_last = self.db.is_stop_saved(stopid)
        # Delete from the saved_stops list, since it should have been already deleted
        self.saved_stops.remove(stopid)
        # Assert
        self.assertTrue(saved_first)
        self.assertFalse(saved_last)

    def test_get_all_saved_stops(self):
        """Use the method to get the Stop IDs of all the saved Stops, and compare with the Stops saved on this test.
        At least all the stops saved while testing must exist on the DB."""
        # Generate 5 new stops, save on DB and on a local list
        stops_created: Dict[int, Stop] = dict()
        for i in range(5):
            stopid = generate_stopid(1, 100, self.saved_stops)
            stop = online_stop_getter(stopid)
            self.db.save_stop(stop)
            stops_created[stopid] = stop
        stops_created_ids = list(stops_created.keys())
        # Get all saved stops on DB
        stops_db = self.db.get_all_saved_stops()
        # Get stops in common (between Saved Stops on DB and Created stops on this test)
        common_stops = list(filter(lambda x: x in stops_created_ids, stops_db))
        # Sort lists
        stops_created_ids.sort()
        common_stops.sort()
        # Assert (common_stops must match stops_created)
        self.assertListEqual(stops_created_ids, common_stops)

    def test_stop_not_exists(self):
        """Search a stop on DB that does not exist, and check if the method throws the StopNotFound exception
        """
        self.assertRaises(StopNotFound, self.db.find_stop, 8080)

    def test_stop_not_exists_online_getter(self):
        """Test of the StopNotExist exception, thrown by the dummy Online Stop Getter
        """
        self.assertRaises(StopNotExist, online_stop_getter, 8080)  # (Exception, function, args)

    def test_stop_not_found_online_getter(self):
        """Test of the StopNotExist exception, thrown by the dummy Offline Stop Getter
        """
        self.assertRaises(StopNotFound, offline_stop_getter, 8080)  # (Exception, function, args)

    def test_stop_getter_unavailable(self):
        """Test of the StopGetterUnavailable exception, thrown by the dummy Unavailable Stop Getter
        """
        self.assertRaises(StopGetterUnavailable, unavailable_stop_getter, 1)  # (Exception, function, args)
