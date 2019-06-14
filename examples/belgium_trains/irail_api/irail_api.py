
# Native libraries
import os
import json
from typing import Dict, List

# Installed libraries
import requests
from pybuses import Stop, Bus
from pybuses.exceptions import *


PATH = os.path.dirname(os.path.abspath(__file__))
STOPS_FILENAME = "irail_stations_short.json"


class IRailAPI:
    def __init__(self):
        with open(os.path.join(PATH, STOPS_FILENAME)) as file:
            self.stations_json_short: Dict = json.load(file)["station"]

    @staticmethod
    def stopid_to_int(original_stopid: str) -> int:
        """Convert a StopID returned by the iRail API to an integer compatible with PyBuses
        :param original_stopid: StopID as string, with the format used by the iRail API
        :return: StopID as integer
        """
        return int(original_stopid.replace("BE.NMBS.", ""))

    @staticmethod
    def stopid_from_int(pybuses_stopid: int) -> str:
        """Convert a PyBuses-compatible integer StopID to the format used by the iRail API
        :param pybuses_stopid: StopID as integer
        :return: StopID as string, with the format used by the iRail API
        """
        return "BE.NMBS.00" + str(pybuses_stopid)

    @staticmethod
    def json_to_stop(js_stop: Dict) -> Stop:
        """Convert a Station JSON object, returned by the iRail API as part of the "station" array on the
        "stations" endpoint, to a PyBuses Stop object
        :param js_stop:
        :return:
        """
        return Stop(
            stopid=IRailAPI.stopid_to_int(js_stop["id"]),
            name=js_stop["standardname"],
            lat=js_stop["locationX"],
            lon=js_stop["locationY"]
        )

    def online_stop_getter(self, stopid: int) -> Stop:
        """The Online getter search for a stop on the result returned by the "stations" endpoint of the iRail API.
        The API does not provide an endpoint to search a single Stop, so it is required to fetch the complete list
        of stops and search for the requested stop on the response.
        This method can be used as a PyBuses Online Stop Getter
        :param stopid: StopID as integer
        :return: PyBuses Stop object
        :raises: StopNotExist if the stop is not found |
                 StopGetterUnavailable if some error happened while requesting the API
        """
        try:
            response = requests.get("https://api.irail.be/stations/?format=json&lang=en")
            if response.status_code != 200:
                raise requests.exceptions.RequestException("Status Code: " + str(response.status_code))
            stops_json: List[Dict] = json.loads(response.text)["station"]
            stopid_str = self.stopid_from_int(stopid)
            stop_json = next(js for js in stops_json if js["id"] == stopid_str)
            return self.json_to_stop(stop_json)
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError, KeyError) as ex:
            raise StopGetterUnavailable(ex)
        except StopIteration:
            raise StopNotExist()

    def offline_stop_getter(self, stopid: int) -> Stop:
        """The Offline getter search for a stop on the "irail_stations_short.json" file,
        which is the result returned by the "stations" endpoint of the iRail API, but with less stops.
        This method can be used as a PyBuses Offline Stop Getter
        :param stopid: StopID as integer
        :return: PyBuses Stop object
        :raises: StopNotFound if the stop is not found
        """
        try:
            stop_json = next(js for js in self.stations_json_short if js["id"] == self.stopid_from_int(stopid))
        except StopIteration:
            raise StopNotFound()
        else:
            return self.json_to_stop(stop_json)

    def bus_getter(self, stopid: int) -> List[Bus]:
        """The Bus Getter search for all the trains arriving to a Station (Stop).
        The API can return up to 50 trains, so this function limit the output to a max of 20 trains.
        This method can be used as a PyBuses Stop Getter
        :param stopid: StopID as integer
        :return: List of Buses (trains) that will arrive to the station
        :raises: BusGetterUnavailable if some error happened while requesting the API
        """
        try:
            response = requests.get(
                f"http://api.irail.be/liveboard/?id={self.stopid_from_int(stopid)}&arrdep=arrival&lang=en&format=json"
            )
            if response.status_code != 200:
                raise requests.exceptions.RequestException("Status Code: " + str(response.status_code))
            response_json = json.loads(response.text)
            # The response return a timestamp when the liveboard was generated,
            # and each train has a timestamp of when it arrives
            response_timestamp = int(response_json["timestamp"])
            trains_json: List[Dict] = json.loads(response.text)["arrivals"]["arrival"]
            buses: List[Bus] = list()
            for i, train_json in enumerate(trains_json):
                if i > 20:
                    break
                # The trains do not have a line and a route, so we use the same information on both fields
                bus = Bus(
                    busid=train_json.get("vehicle"),
                    line=train_json["station"],
                    route=train_json["station"],
                    time=int(((int(train_json["time"]) - response_timestamp) / 60) + 0.5)
                )
                buses.append(bus)
                # TODO add extra available info on extra fields?
            return buses
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError, KeyError, ValueError) as ex:
            raise StopGetterUnavailable(ex)
