
from Logging import logging, create_logger

init_log = create_logger(
    name="PyBuses",
    db_name="Databases/PyBusesLog.sqlite",
    db_level=logging.DEBUG,
    print_level=logging.DEBUG
)

db_log = create_logger(
    name="PyBuses_DB",
    db_name="Databases/PyBusesLog.sqlite",
    db_level=logging.DEBUG,
    print_level=logging.DEBUG
)

cache_log = create_logger(
    name="PyBuses_Cache",
    db_name="Databases/PyBusesLog.sqlite",
    db_level=logging.INFO,
    print_level=logging.INFO
)

streetview_log = create_logger(
    name="PyBuses_StreetView",
    db_name="Databases/PyBusesLog.sqlite",
    db_level=logging.DEBUG,
    print_level=logging.DEBUG
)

maps_log = create_logger(
    name="PyBuses_Maps",
    db_name="Databases/PyBusesLog.sqlite",
    db_level=logging.DEBUG,
    print_level=logging.DEBUG
)
