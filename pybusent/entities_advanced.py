
# # Native # #
from datetime import datetime, timedelta, tzinfo
from typing import Optional, List

# # Package # #
from .entities import Stop, Bus, Stops, BusTime
from .helpers import *

__all__ = ("AdvancedStop", "AdvancedBus")


class AdvancedStop(Stop):
    """Stop to where Buses will arrive.
    This AdvancedStop has more attributes than the base Stop:
    - created: datetime when this Stop was first registered
    - updated: datetime when this Stop was last updated
    - original_name: original Stop name from an external data source
    - tags: list of extra tags for this Stop
    - extra_names: list of extra names for this Stop
    """
    created: Optional[datetime]
    updated: Optional[datetime]
    original_name: Optional[str]
    tags: List[str] = []
    extra_names: List[str] = []
    distance: Optional[float]


class AdvancedBus(Bus):
    """This AdvancedBus has more attributes than the base Bus:
    - arrival: absolute or relative time until arrival to the Stop
    - departure: absolute or relative time until departure from the Stop
    - stops: list of stops this bus will stop at (used for Static bus definitions)
    """
    arrival: BusTime
    departure: BusTime
    stops: Stops

    def relative_arrival(self, timezone: Optional[tzinfo]) -> timedelta:
        """Get the time difference between current time and the 'arrival' of this Bus (must be a relative datetime).
        A custom timezone can be used for the current time, otherwise default 'datetime' parameter is system timezone.
        """
        return calculate_relative_time(self.arrival, timezone)

    def relative_departure(self, timezone: Optional[tzinfo]) -> timedelta:
        """Get the time difference between current time and the 'departure' of this Bus (must be a relative datetime).
        A custom timezone can be used for the current time, otherwise default 'datetime' parameter is system timezone.
        """
        return calculate_relative_time(self.departure, timezone)

    def time_in_stop(self) -> timedelta:
        """Get the difference of time between the departure and the arrival time"""
        return self.departure - self.arrival
