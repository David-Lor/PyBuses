
#Native libraries
import requests
#Own modules
from .Logger import maps_log as log


MAPS_API_URL = "https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=17&scale=2&size={sizeX}x{sizeY}&maptype={maptype}&format=png&visual_refresh=true&markers=size:mid%7Ccolor:0x0ba037%7Clabel:%7C{lat},{lon}"
MAPTYPE_NORMAL = "roadmap"
MAPTYPE_TERRAIN = "hybrid"
#Max image size: 640x640
MAPS_IMAGESIZE_X_HORIZONTAL = 600
MAPS_IMAGESIZE_Y_HORIZONTAL = 300
MAPS_IMAGESIZE_X_VERTICAL = 325
MAPS_IMAGESIZE_Y_VERTICAL = 400

class GoogleMaps(object):
    def __init__(self, db):
        """
        :param db: Database object
        """
        self.db = db
        self.db.write("""CREATE TABLE IF NOT EXISTS maps(
            stopid UNSIGNED INTEGER,
            fileid TEXT NOT NULL,
            vertical BOOLEAN NOT NULL,
            terrain BOOLEAN NOT NULL,
            created TEXT,
            PRIMARY KEY (stopid, vertical, terrain)
        )""")
    
    def get_maps_live(self, stop, vertical, terrain, sizeX=None, sizeY=None):
        """Get a Google Maps image of the desired stop from GMaps API.
        This function does not check if the Stop queried Streetview image was already fetched and saved in DB.
        The stop must have a valid location (it is not checked here).
        :param stop: Stop object to get maps from
        :param vertical: if True, get vertical image; if False, get horizontal image
        :param terrain: if True, get terrain image; if False, get normal map
        :param sizeX: Horizontal size of image (default *)
        :param sizeY: Vertical size of image (default *)
        :return: Bytes object of the fetched StreetView image
        * Both sizes use constant MAPS_IMAGESIZE_X/Y_HORIZONTAL/VERTICAL variables from the module as default values.
        """
        if sizeX is None or sizeY is None:
            if vertical:
                sizeX = MAPS_IMAGESIZE_X_VERTICAL
                sizeY = MAPS_IMAGESIZE_Y_VERTICAL
            else:
                sizeX = MAPS_IMAGESIZE_X_HORIZONTAL
                sizeY = MAPS_IMAGESIZE_Y_HORIZONTAL
        url = MAPS_API_URL.format(
            sizeX=sizeX,
            sizeY=sizeY,
            lat=stop.lat,
            lon=stop.lon,
            maptype=MAPTYPE_TERRAIN if terrain else MAPTYPE_NORMAL
        )
        log.debug("Getting StreetView image from URL:" + url)
        return requests.get(url).content

    def save_maps_db(self, stopid, fileid, vertical, terrain):
        """Save a Maps image of a Stop in local DB.
        This method must be called from the Telegram module when a picture has been sent.
        :param stopid: Stop ID/Number of the stop related with the StreetView image
        :param fileid: FileID returned by Telegram when image was originally sent
        :param vertical: set to True if image is vertical
        :param terrain: set to True is map is terrain-view (satellite hybrid)
        """
        self.db.write(
            "INSERT OR IGNORE INTO maps (stopid, fileid, vertical, terrain, created) VALUES (?,?,?,?,?)",
            (stopid, fileid, int(vertical), int(terrain), self.db.curdate())
        )
    
    def search_maps_db(self, stopid, vertical, terrain):
        """Search for a Maps image of the desired stop in local DB.
        :param stopid: Stop ID/Number to get StreetView image of
        :param vertical: True to search vertical images, False for horizontal
        :param terrain: True to search terrain/satellite images, False for normal map
        :return: Telegram FileID, if stop was saved in DB
        :return: None if no image was found in DB for that stopid
        """
        return self.db.read(
            "SELECT fileid FROM maps WHERE stopid=? AND vertical=? AND terrain=?",
            variables=(stopid, int(vertical), int(terrain)),
            fetchall=False,
            single_column=True
        )
    
    def get_maps(self, stop, vertical=True, terrain=False):
        """Get a Google Maps image for the desired stop from local DB or GMaps API.
        The function searches first on the DB for the SV image (Telegram File ID)
        If it's not saved there, the image is fetched from GMaps API and returned as Bytes.
        Telegram send_photo method used by the source module must accept FileID AND Bytes.
        :param stop: Stop object to get Maps from (Must have Lat&Lon!)
        :param vertical: if True, get vertical image; if False, get horizontal image (default=True - vertical)
        :param terrain: if True, get terrain image; if False, get normal map (default=False - normal map)
        :return: FileID if image is saved in DB
        :return: Bytes if image is not saved in DB
        """
        log.info("Getting Maps image for Stop #{} (Vertical={}; Terrain={})".format(stop.id, vertical, terrain))
        try:
            imageid = self.search_maps_db(stop.id, vertical, terrain)
            if imageid is None:
                return self.get_maps_live(stop, vertical, terrain)
            else:
                return imageid
        except Exception:
            log.exception("Could not get Maps image for Stop #{}".format(stop.id))
