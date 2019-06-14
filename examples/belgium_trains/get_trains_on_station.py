import sys
import logging

from pybuses import PyBuses
from pybuses.exceptions import *

try:
    from .irail_api import IRailAPI
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from irail_api import IRailAPI

logger = logging.getLogger("pybuses")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

api = IRailAPI()
pybuses = PyBuses()

pybuses.add_stop_getter(api.online_stop_getter, online=True)
pybuses.add_stop_getter(api.offline_stop_getter, online=False)
pybuses.add_bus_getter(api.bus_getter)


if __name__ == '__main__':
    while True:
        try:
            stopid_str = input("Enter a StopID to search (Ctrl+C or q to exit): ")
            if stopid_str.lower().strip() == "q":
                raise KeyboardInterrupt()
            stopid = int(stopid_str)
            stop = pybuses.find_stop(stopid)
            buses = pybuses.get_buses(stopid)
        except ValueError:
            print("The entered StopID was incorrect, try again")
        except (KeyboardInterrupt, InterruptedError):
            break
        except StopGetterUnavailable as ex:
            print("The Stop Getter is unavailable, please try again later.", "We got this error:", ex, sep="\n")
        except (StopNotFound, StopNotExist):
            print("The Stop does not exist")
        else:
            print("Stop found!")
            print("ID:", stop.stopid)
            print("Name:", stop.name)
            if stop.has_location():
                print("Latitude:", stop.lat)
                print("Longitude:", stop.lon)
            print("-----------------------------")
            print(len(buses), "trains arriving to this station:")
            for bus in buses:
                print(
                    f" - {bus.line} (Train {bus.busid}): "
                    f"{bus.time} minutes {'remaining' if bus.time >= 0 else 'ago'}"
                )
            print("-----------------------------")
    print("Bye!")
