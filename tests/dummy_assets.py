
# Native libraries
import random
import hashlib
import _hashlib
from typing import Optional, Tuple, Dict, List

# PyBuses modules
from pybuses.assets import *
from pybuses.exceptions import *

_FAKE_STREETS = {
    1: "Canterbury Drive, 123",
    2: "Academy Street, 154",
    3: "Hickory Lane, 277",
    4: "Morris Street, 149",
    5: "Main Street, 217",
    6: "Penn Street, 172",
    7: "Sherman Street, 185",
    8: "Clay Street, 202",
    9: "Railroad Street, 299",
    10: "Route 11, 209",
    11: "Aspen Court, 28",
    12: "Hawthorne Lane, 164",
    13: "3rd Street North, 90",
    14: "Willow Avenue, 96",
    15: "Manor Drive, 8",
    16: "Oxford Court, 157",
    17: "Park Avenue, 54",
    18: "Lawrence Street, 20",
    19: "Arch Street, 195",
    20: "Dogwood Lane, 83",
    21: "Maple Street, 254",
    22: "Route 32, 76",
    23: "School Street, 120",
    24: "1st Street, 114",
    25: "East Avenue, 27",
    26: "College Street, 280",
    27: "Glenwood Drive, 300",
    28: "York Street, 165",
    29: "Clinton Street, 300",
    30: "Shady Lane, 155",
    31: "Ridge Avenue, 44",
    32: "West Street, 13",
    33: "Hawthorne Avenue, 221",
    34: "Laurel Lane, 209",
    35: "Route 4, 159",
    36: "4th Street West, 38",
    37: "Overlook Circle, 216",
    38: "Rosewood Drive, 299",
    39: "Broad Street, 298",
    40: "Cross Street, 297",
    41: "Lantern Lane, 232",
    42: "Magnolia Court, 128",
    43: "5th Avenue, 65",
    44: "Wood Street, 179",
    45: "Route 6, 125",
    46: "Cambridge Road, 294",
    47: "Chestnut Avenue, 283",
    48: "Route 64, 188",
    49: "4th Street, 122",
    50: "Meadow Street, 250",
    51: "Tanglewood Drive, 288",
    52: "Maiden Lane, 300",
    53: "Willow Street, 290",
    54: "Park Drive, 45",
    55: "Windsor Drive, 109",
    56: "Sunset Drive, 25",
    57: "Winding Way, 26",
    58: "Center Street, 35",
    59: "Route 5, 148",
    60: "Devonshire Drive, 299",
    61: "Oak Street, 223",
    62: "Garden Street, 148",
    63: "Belmont Avenue, 38",
    64: "4th Street South, 259",
    65: "Bank Street, 275",
    66: "Delaware Avenue, 162",
    67: "Hillcrest Drive, 95",
    68: "Holly Drive, 142",
    69: "4th Street North, 289",
    70: "State Street, 127",
    71: "Sycamore Street, 18",
    72: "Parker Street, 195",
    73: "10th Street, 156",
    74: "Chestnut Street, 111",
    75: "12th Street, 166",
    76: "11th Street, 60",
    77: "Lilac Lane, 72",
    78: "Country Lane, 105",
    79: "Front Street South, 223",
    80: "Williams Street, 279",
    81: "Hilltop Road, 239",
    82: "Lincoln Avenue, 289",
    83: "Inverness Drive, 24",
    84: "Briarwood Drive, 86",
    85: "Harrison Avenue, 294",
    86: "5th Street South, 216",
    87: "Warren Street, 296",
    88: "Spruce Avenue, 19",
    89: "North Avenue, 101",
    90: "Somerset Drive, 144",
    91: "Woodland Road, 137",
    92: "Magnolia Drive, 128",
    93: "Evergreen Drive, 121",
    94: "6th Street, 140",
    95: "Elmwood Avenue, 6",
    96: "State Street East, 203",
    97: "Buttonwood Drive, 28",
    98: "Pennsylvania Avenue, 263",
    99: "Schoolhouse Lane, 245",
    100: "Church Street South, 255"
}

"""STOPS
IDs: from 1 to 100
- Stops without Location, without Other: 1 to 20
- Stops with Location, without Other: 21 to 50
- Stops with Location, with Other: 51 to 70
- Stops without Location, with Other: 71 to 100
"""


def _generate_location(stopid: int) -> Optional[Tuple[float, float]]:
    if 21 <= stopid <= 70:
        lat = random.uniform(-90, 90)
        lon = random.uniform(-180, 180)
        return lat, lon
    else:
        return None


def _generate_other(stopid: int) -> Optional[Dict]:
    if 51 <= stopid <= 100:
        d = dict()
        random_numbers = [random.randint(x, 1000) for x in range(10)]
        sha256: _hashlib.HASH = hashlib.sha256()
        for i, x in enumerate(random_numbers, 1):
            sha256.update(str(x).encode())
            digest = sha256.hexdigest()
            d[f"random_data_{i}"] = digest
        return d
    else:
        return None


def _stop_getter(stopid: int, online: bool) -> Stop:
    try:
        name = _FAKE_STREETS[stopid]
    except KeyError:
        if online:
            raise StopNotExist(f"Stop {stopid} does not exist")
        else:
            raise StopNotFound(f"Stop {stopid} not found on this getter")
    stop = Stop(stopid, name)
    location = _generate_location(stopid)
    other = _generate_other(stopid)
    if location:
        stop.lat = location[0]
        stop.lon = location[1]
    if other:
        stop.other = other
    return stop


def online_stop_getter(stopid: int) -> Stop:
    """A fake external Online Stop Getter function used by PyBuses as a Stop Getter
    :param stopid: ID of the Stop to get
    :return: Stop object
    :raise: StopNotExist if the Stop does not exist
    """
    return _stop_getter(stopid, True)


def offline_stop_getter(stopid: int) -> Stop:
    """A fake external Offline Stop Getter function used by PyBuses as a Stop Getter
    :param stopid: ID of the Stop to get
    :return: Stop object
    :raise: StopNotFound if the Stop if not available on this getter
    """
    return _stop_getter(stopid, False)


def unavailable_stop_getter(stopid: int) -> Stop:
    """A fake external Stop Getter function used by PyBuses as a Stop Getter,
    that is not available and throws the StopGetterUnavailable exception.
    :param stopid: ID of the Stop to get
    :return: Stop object, but it always raises the StopGetterUnavailable exception
    :raise: (always) StopGetterUnavailable
    """
    raise StopGetterUnavailable(f"Simulated StopGetterUnavailable exception for Stop #{stopid}")


class GenericSource:
    """A generic class that provides generic functions compatible with PyBuses:
        - Stop Getter
        - Stop Setter
        - Stop Deleter
        - Bus Getter
        - Bus Setter (*)
        - Bus Deleter (*)
    Stops are saved on a list of Stop objects.
    Buses are saved on a dict {stopid: buses}, being buses a list of Bus objects, for each stop.
    (*) = since these methods are not implemented yet on PyBuses, they are used only for setUp the testing test cases,
          so they do not follow any PyBuses standards, since these are not defined yet.
    """
    def __init__(self):
        self.stops: List[Stop] = list()
        self.buses: Dict[int, List[Bus]] = dict()

    def __add_stop(self, stop: Stop):
        self.stops.append(stop)
        self.buses[stop.stopid] = list()

    def __delete_stop_by_id(self, stopid: int):
        self.stops.remove(next(iter_stop for iter_stop in self.stops if iter_stop.stopid == stopid))
        self.buses.pop(stopid)

    def stop_getter(self, stopid: int, online: bool):
        try:
            return next(stop for stop in self.stops if stop.stopid == stopid)
        except StopIteration:
            if online:
                raise StopNotExist()
            else:
                raise StopNotFound()

    def online_stop_getter(self, stopid: int):
        return self.stop_getter(stopid, True)

    def offline_stop_getter(self, stopid: int):
        return self.stop_getter(stopid, False)

    def stop_exists(self, stopid: int) -> bool:
        return any(stop for stop in self.stops if stopid == stopid)

    def stop_setter(self, stop: Stop, update: bool):
        saved = self.stop_exists(stop.stopid)
        # TODO saved, updated timestamps??? not required by PyBuses standars?
        if not saved:
            # New stop
            self.stops.append(stop)
        elif update:
            # Stop exists, update (replace) it
            self.__delete_stop_by_id(stop.stopid)
            self.stops.append(stop)
        else:
            # Stop exists, do not update it
            pass

    def stop_deleter(self, stopid: int) -> bool:
        try:
            self.__delete_stop_by_id(stopid)
        except StopIteration:
            return False
        else:
            return True

    def bus_getter(self, stopid: int) -> List[Bus]:
        try:
            return self.buses[stopid]
        except KeyError:
            raise StopNotFound()

    def bus_setter(self, *args: Bus, stopid: int):
        # Not used by PyBuses
        self.buses[stopid].extend(args)

    def bus_deleter(self, *args: Bus, stopid: int):
        # Not used by PyBuses
        for bus in args:
            if bus in self.buses[stopid]:
                self.buses[stopid].remove(bus)

    def broken_stop_getter(self, stopid: int):
        raise StopGetterUnavailable("This dummy method always throws StopGetterUnavailable")

    def broken_stop_setter(self, stop: Stop, update: bool):
        raise StopSetterUnavailable("This dummy method always throws StopSetterUnavailable")
