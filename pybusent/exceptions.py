"""EXCEPTIONS
Custom exceptions for issues related with the Stops and Buses
"""


class PyBusesException(Exception):
    """Base exception for all the custom PyBusesEntieies exceptions
    """
    pass


class StopException(PyBusesException):
    """Base exception for all the Stop-related exceptions
    """
    pass


class StopNotFound(StopException):
    """Exception raised when a Stop is Not Found on a certain data source,
    but it might exist on other data sources
    """
    pass


class StopNotExist(StopException):
    """Exception raised when a trustful data source confirms that a Stop not exist physically
    """
    pass


class BusException(PyBusesException):
    """Base exception for all the Bus-related exceptions
    """
    pass
