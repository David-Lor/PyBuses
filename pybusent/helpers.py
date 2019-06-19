"""HELPERS
Helper functions for class methods
"""

# # Native # #
import hashlib
import copy
from typing import Optional, Dict
from datetime import datetime, timedelta, tzinfo

__all__ = ("calculate_relative_time", "generate_busid", "clear_dict_values")


def calculate_relative_time(timestamp: datetime, timezone: Optional[tzinfo] = None) -> timedelta:
    """Get the time difference between current time and the given time.
    A custom timezone can be used for the current time, otherwise default 'datetime' parameter is system timezone.
    """
    return datetime.now(tz=timezone) - timestamp


def generate_busid(line: str, route: str) -> str:
    """Generate a Bus ID given its line and route.
    Bus ID is generated as a MD5 checksum from the line and route, and returned as string.
    If line or route not exist, they will be ignored. Is both not exist, all Buses will have the same Bus ID.
    """
    h = hashlib.md5()
    if line:
        h.update(line.encode())
    if route:
        h.update(route.encode())
    return h.hexdigest()


def clear_dict_values(
        d: Dict,
        remove_none: bool,
        remove_empty_strings: bool,
        remove_empty_lists: bool,
        remove_empty_dicts: bool
) -> Dict:
    """Given a Dict, clear the Values that are null (None) or empty strings, depending on the function params.
    A copy of the given dict is returned.
    """
    cloned_dict = copy.deepcopy(d)
    for key, value in d.items():
        conditions = (
            remove_none and value is None,
            remove_empty_strings and value == "",
            remove_empty_lists and isinstance(value, list) and not value,
            remove_empty_dicts and isinstance(value, dict) and not value
        )
        if any(conditions):
            cloned_dict.pop(key)
        elif isinstance(value, dict):
            cloned_dict[key] = clear_dict_values(
                value, remove_none, remove_empty_strings, remove_empty_lists, remove_empty_dicts
            )

    return cloned_dict
