#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of WAQD
# (see https://github.com/goszpeti/WeatherAirQualityDevice).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from waqd.base.network import Network
from waqd.base.file_logger import Logger
import urllib.request
import json

class OpenTopoData():
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
        if location_data and location_data.get("lat") == latitude and location_data.get("lng") == longitude:
            return self._altitude_info.get("elevation", 0.0)

        # wait a little bit for connection
        is_connected = Network().wait_for_internet()
        if not is_connected:
            Logger().error("OpenTopo: Timeout while wating for network connection")
            return 0
        response_file = None
        try:
            response_file = urllib.request.urlretrieve(
                self.QUERY.format(lat=latitude, long=longitude))
        except Exception as error:
            Logger().error(f"OpenTopo: Can't get altitude for {latitude} {longitude} : {str(error)}")

        if not response_file:
            return 0

        with open(response_file[0], encoding="utf-8") as response_json:
            response = json.load(response_json)
            if response.get("status", "") != "OK":
                return 0
            self._altitude_info = response.get("results")[0]  # TODO guard
            return self._altitude_info.get("elevation")