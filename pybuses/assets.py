
# Native libraries
import json
import hashlib
from typing import Union, Optional, Dict

__all__ = ("Bus", "Stop")


class Bus(object):
    """A Bus that will arrive to a Stop, or that is available on the bus service as a line-route."""
    def __init__(
            self,
            line: str,
            route: str,
            time: Optional[Union[int, float]] = None,
            distance: Optional[Union[int, float]] = None,
            busid: Optional[str] = None,
            other: Optional[Dict] = None,
            auto_parse_other: bool = True
    ):
        """A Bus
        :param line: bus line (required)
        :param route: bus route (required)
        :param time: bus remaining time for reaching stop (optional, default=None)
        :param distance: bus distance to stop (optional, default=None)
        :param busid: bus ID (optional, default=None, is auto generated on init)
        :param other: additional data for the Bus object, as a dict (optional, default=empty dict)
        :param auto_parse_other: if True, automatically parse the "other" attribute to convert to a Dict (default=True)
        :type line: str
        :type route: str
        :type time: int or float or None
        :type distance: int or float or None
        :type busid: str
        :type other: dict
        :type auto_parse_other: bool
        .. note:: Line and Route values will be casted and strip on __init__
        """
        self.line: str = str(line).strip()
        self.route: str = str(route).strip()
        self.time: Optional[Union[int, float]] = time
        self.distance: Optional[Union[int, float]] = distance
        self.auto_parse_other = auto_parse_other
        self.other: Dict = other if other is not None else dict()
        if busid is None:
            md5 = hashlib.md5()
            md5.update(self.line.encode())
            md5.update(self.route.encode())
            self.busid = md5.hexdigest()
        else:
            self.busid = str(busid)

    def asdict(self) -> Dict:
        """Return all the data available about this Bus as a dict.
        Parameters where values are None will be hidden.
        :return: all parameters of this Bus object as a dict
        :rtype: dict
        """
        return _clean_dict(self.__dict__)

    def __iter__(self):
        for k, v in self.asdict().items():
            yield k, v

    def __str__(self):
        return "Bus" + str(self.asdict())

    def __setattr__(self, key, value):
        if key == "other" and self.auto_parse_other and type(value) is str:
            self.other = json.loads(value.replace("'", '"'))
        else:
            object.__setattr__(self, key, value)


class Stop(object):
    """A bus Stop, identified by a Stop ID. Buses will arrive to it."""
    auto_parse_other = False

    def __init__(
            self,
            stopid: Union[int, str],
            name: str,
            lat: Union[float, str, None] = None,
            lon: Union[float, str, None] = None,
            other: Optional[Dict] = None,
            auto_parse_other: bool = True
            # TODO add "saved", "updated" datetime attributes?
    ):
        """
        :param stopid: Stop ID/Number (required)
        :param name: Stop name (required)
        :param lat: Stop location latitude (optional, default=None)
        :param lon: Stop location longitude (optional, default=None)
        :param other: additional data for the Stop object, as a dict (optional, default=empty dict)
        :param auto_parse_other: if True, automatically parse the "other" attribute to convert to a Dict (default=True)
        :type stopid: int
        :type name: str
        :type lat: float or None
        :type lon: float or None
        :type other: dict
        :type auto_parse_other: bool
        .. note:: StopID, Lat and Lon values will be casted on __init__
        .. note:: Stop Name will be strip on __init__
        .. note:: Lat and Lon are both required
        """
        self.auto_parse_other: bool = auto_parse_other
        self.stopid: int = int(stopid)
        self.name: str = name.strip()
        self.other: Dict = other if other is not None else dict()
        self.lat: Optional[float] = None
        self.lon: Optional[float] = None
        if (lat, lon) != (None, None):
            self.lat: float = float(lat)
            self.lon: float = float(lon)

    def has_location(self) -> bool:
        """Check if this Stop has a valid location set (latitude and longitude).
        :return: True if Stop has both Latitude & Longitude values, False if one or both are missing
        :rtype: bool
        """
        return not (self.lat, self.lon) == (None, None)

    def asdict(self):
        """Return all the data available about this Stop as a dict.
        Parameters where values are None will be hidden.
        :return: all parameters of this Stop object as a dict
        :rtype: dict
        """
        d = _clean_dict(self.__dict__)
        d.pop("auto_parse_other")
        return d

    def __iter__(self):
        for k, v in self.asdict().items():
            yield k, v

    def __str__(self):
        return "Stop" + str(self.asdict())

    def __setattr__(self, key, value):
        if key == "other" and self.auto_parse_other and type(value) is str:
            self.other = json.loads(value.replace("'", '"'))
        else:
            object.__setattr__(self, key, value)


def _clean_dict(d: Dict) -> Dict:
    """Remove null (None) elements from a dictionary.
    :param d: original dict to analyze
    :type d: dict
    :return: copy of d, but keys with null values are removed
    :rtype: dict
    """
    dc = d.copy()
    for k, v in d.items():
        if v is None:
            dc.pop(k)
    return dc
