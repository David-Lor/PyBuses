
# Native libraries
import random
import functools
from typing import List


def generate_stopid(start: int, end: int, created: List[int]) -> int:
    """Generate a random StopID between the given range, avoiding repeated values on the given list.
    :param start: Start of the range (inclusive)
    :param end: End of the range (inclusive)
    :param created: List of already generated StopIDs, to avoid generating a value that already exists
    :type start: int
    :type end: int
    :type created: List[int]
    :return: Generated StopID
    :rtype: int
    """
    stopid = None
    while stopid is None or (type(stopid) is int and stopid in created):
        stopid = random.randint(start, end)
    created.append(stopid)
    return stopid


def log_method(function, log):
    """Decorator for the "test_" methods in TestCase class.
    Log that the test is starting, since Unittest does not provide
    setUp/tearDown methods with the processing function as attribute.
    :param function: Function to decorate
    :param log: logger
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        docstring = function.__doc__
        if docstring:
            if isinstance(docstring, bytes):
                docstring = docstring.decode()
            docstring = " ".join(docstring.split()).strip()
        else:
            docstring = function.__name__
        log.info("Starting " + docstring + "...")
        return function(*args, **kwargs)
    return wrapper
