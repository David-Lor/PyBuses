"""SORTING
Functions to sort lists of objects by one of their attributes
"""

__all__ = ("BusSort",)


class BusSort:
    """Keys to sort lists of buses
    """

    @staticmethod
    def line(bus):
        """Key to sort a list of buses by their Line
        """
        return bus.line

    @staticmethod
    def route(bus):
        """Key to sort a list of buses by their Route
        """
        return bus.route

    @staticmethod
    def line_route(bus):
        """Key to sort a list of buses by their Line, then by their Route
        """
        return bus.line, bus.route

    @staticmethod
    def time(bus):
        """Key to sort a list of buses by their Time
        """
        return bus.time

    @staticmethod
    def time_line(bus):
        """Key to sort a list of buses by their Time, then by their Line
        """
        return bus.time, bus.line

    @staticmethod
    def time_route(bus):
        """Key to sort a list of buses by their Time, then by their Route
        """
        return bus.time, bus.route

    @staticmethod
    def time_line_route(bus):
        """Key to sort a list of buses by their Time, then by their Line, then by their Route
        """
        return bus.time, bus.line, bus.route

    @staticmethod
    def arrival(bus):
        """Key to sort a list of buses by their Arrival Time
        """
        return bus.arrival

    @staticmethod
    def departure(bus):
        """Key to sort a list of buses by their Departure Time
        """
        return bus.departure
