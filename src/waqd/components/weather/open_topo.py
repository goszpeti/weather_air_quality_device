from waqd.base.network import Network
from waqd.base.file_logger import Logger
import urllib.request
import json


class OpenTopoData:
    """
    Get altitude (elevation) from geo coordinates.
    Needed for OpenWeatherMap)
    """

    QUERY = "https://api.opentopodata.org/v1/eudem25m?locations={lat},{long}"

    def __init__(self):
        super().__init__()
        self._altitude_info = {}

    def get_altitude(self, latitude: float, longitude: float) -> float:
        location_data = self._altitude_info.get("location")
        if (
            location_data
            and location_data.get("lat") == latitude
            and location_data.get("lng") == longitude
        ):
            return self._altitude_info.get("elevation", 0.0)

        # wait a little bit for connection
        is_connected = Network().wait_for_internet()
        if not is_connected:
            Logger().error("OpenTopo: Timeout while wating for network connection")
            return 0
        response_file = None
        try:
            response_file = urllib.request.urlretrieve(
                self.QUERY.format(lat=latitude, long=longitude)
            )
        except Exception as error:
            Logger().error(
                f"OpenTopo: Can't get altitude for {latitude} {longitude} : {str(error)}"
            )

        if not response_file:
            return 0

        with open(response_file[0], encoding="utf-8") as response_json:
            response = json.load(response_json)
            if response.get("status", "") != "OK":
                return 0
            self._altitude_info = response.get("results")[0]  # TODO guard
            return self._altitude_info.get("elevation")
