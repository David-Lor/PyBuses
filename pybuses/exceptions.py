
# Installed libraries
from pymongo.errors import PyMongoError


# # #
# GENERIC PYBUSES EXCEPTION
# # #


class PyBusesException(Exception):
    """Parent exception for ALL the PyBuses custom exceptions."""
    pass


# # #
# INSIDE PYBUSES EXCEPTIONS
# # #


class PyBusesBuildError(PyBusesException):
    """Raised when some parameters of a PyBuses instance, required for the current operation,
    are missing or misformed."""
    pass


class GetterException(PyBusesException, IOError):
    """Parent exception of ALL the Getter functions."""
    pass


class SetterException(PyBusesException, IOError):
    """Parent exception of ALL the Setter functions."""
    pass


class DeleterException(PyBusesException, IOError):
    """Parent exception of ALL the Deleter functions."""
    pass


class MissingGetters(PyBusesBuildError, GetterException):
    """Raised when trying to fetch attributes of an asset when any of the required Getters is defined."""
    pass


class MissingSetters(PyBusesBuildError, SetterException):
    """Raised when trying to store attributes of an asset when any of the required Setters is defined."""
    pass


class MissingDeleters(PyBusesBuildError, DeleterException):
    """Raised when trying to delete attributes of an asset when any of the required Deleters is defined."""
    pass


class ResourceUnavailable(PyBusesException, IOError):
    """Generic exception for any outside I/O resource that is not available or failed."""
    pass


class GetterResourceUnavailable(GetterException, ResourceUnavailable):
    """Raised when the read operation on a resource accessed from a Getter failed."""
    pass


class SetterResourceUnavailable(SetterException, ResourceUnavailable):
    """Raised when the write operation on a resource accessed from a Setter failed."""
    pass


class DeleterResourceUnavailable(DeleterException, ResourceUnavailable):
    """Raised when the write operation on a resource accessed from a Deleter failed."""
    pass


# # #
# STOP EXCEPTIONS
# # #


class StopException(PyBusesException):
    """Parent exception for ALL the Stop assets."""
    pass


class StopNotFound(StopException, GetterException):
    """Raised when a Stop is not found on a certain Stop Getter, but it might exist on other Getters."""
    pass


class StopNotExist(StopException, GetterException):
    """Raised when a Stop Getter reported that a stop does not physically exists."""
    pass


class StopGetterUnavailable(GetterResourceUnavailable, StopException):
    """Raised when a Stop Getter is not available or failed."""
    pass


class StopSetterUnavailable(SetterResourceUnavailable, StopException):
    """Raised when a Stop Setter is not available or failed."""
    pass


class StopDeleterUnavailable(DeleterResourceUnavailable, StopException):
    """Raised when a Stop Deleter is not available or failed."""
    pass


# # #
# BUS EXCEPTIONS
# # #


class BusException(PyBusesException):
    """Parent exception for ALL the Bus assets."""
    pass


class BusGetterUnavailable(GetterResourceUnavailable, BusException):
    """Raised when a Bus getter is not available or failed."""
    pass


class BusSetterUnavailable(SetterResourceUnavailable, BusException):
    """Raised when a Bus Setter is not available or failed."""
    pass


class BusDeleterUnavailable(DeleterResourceUnavailable, BusException):
    """Raised when a Bus Deleter is not available or failed."""
    pass

# # #
# MONGODB EXCEPTIONS
# # #


class MongoDBUnavailable(ResourceUnavailable, PyMongoError):
    """Custom exception for errors on the MongoDB class of PyBuses, when the Mongo DB server is unavailable."""
    pass
