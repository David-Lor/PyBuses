
class Bus(object):
    def __init__(self, line, route, time, distance=None):
        """
        :param line: bus line
        :param route: bus route
        :param time: bus remaining time for reaching stop (int)
        :param distance: bus distance to stop (optional, default=None)
        """
        self.line = str(line)
        self.route = str(route)
        self.time = int(time)
        if distance is not None:
            self.distance = float(distance)
        else:
            self.distance = None

class Stop(object):
    def __init__(self, stopid, name, lat=None, lon=None):
        """
        :param stopid: Stop ID/Number (int, required)
        :param name: Stop name (string, not required for reference to custom stop getters)
        :param lat: Stop location latitude (float, optional)
        :param lon: Stop location longitude (float, optional)
        All data types will be casted.
        """
        self.id = int(stopid)
        self.stopid = self.id
        self.name = str(name) if name else None
        if (lat, lon) == (None, None):
            self.lat = None
            self.lon = None
        else:
            self.lat = float(lat)
            self.lon = float(lon)

    def has_location(self):
        return not (self.lat, self.lon) == (None, None)
