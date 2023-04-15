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
"""
This file contains generic classes concerning online weather data.
"""

from datetime import datetime, time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List

from waqd.assets import get_asset_file


def is_daytime(sunrise, sunset, date_time=None):
    """
    Helper function to determine if specified time is day or night
    """
    if date_time is None:
        date_time = datetime.now()
    return sunrise < date_time.time() < sunset


@dataclass
class Location():
    name: str
    country: str
    state: str
    county: str
    postcodes: List[str]
    altitude: float
    latitude: float
    longitude: float


@dataclass
class Weather():
    """
    This class is used to abstract from weather hosting types.
    Relies heavily on OpenWeather data structure
    """
    main: str  # condition name
    wid: int # provider specific weather id 
    # description: str  # condition detail TODO deprecate
    date_time: datetime  # time of the point or day
    fetch_time: datetime = field(init=False)
    icon: str  # icon name
    wind_speed: float  # m/s
    wind_deg: float
    sunrise: time
    sunset: time
    pressure: float  # hPa
    pressure_sea_level: float  # = 1013 # default, TODO deprecate (or the other?)
    humidity: float  # percent
    clouds: float  # percent cloudiness TODO deprecate
    temp: float  # degC
    altitude: float  # elevation of location in meters, deprecated, use from location instead

    def __post_init__(self):
        if self.main:  # only set fetch_time if it is non-empty initiallized
            self.fetch_time = datetime.now()

    def is_daytime(self):
        """
        Helper function to determine if specified time is day or night
        """
        return is_daytime(self.sunrise, self.sunset, self.date_time)

    def get_background_image(self):
        # set weather description specific background image
        online_weather_category = self.main.lower()
        cloudiness = self.clouds

        if cloudiness > 65 and online_weather_category == "clouds":
            online_weather_category = "heavy_clouds"

        if self.is_daytime():
            bg_name = "bg_day_" + online_weather_category
        else:
            bg_name = "bg_night_" + online_weather_category
        return get_asset_file("weather_bgrs", bg_name)

    def get_icon(self) -> Path:
        """
        Helper function to get icon from condition.
        If ident is empty, it uses it's own id to determine the condition.
        """
        file_path = get_asset_file("weather_icons", self.icon)

        # normalize to lower case
        if not file_path:
            file_path = get_asset_file("gui_base", "dummy.png")
        return file_path


@dataclass
class DailyWeather(Weather):
    temp_min: float = field(init=False)
    temp_max: float = field(init=False)
    temp_night_min: float = field(init=False)
    temp_night_max: float = field(init=False)


class BeaufortScale(Enum):
    """ Wind severity mapping to max m/s """
    CALM = 0.5
    LIGHT_AIR = 1.5
    LIGHT_BREEZE = 3.3
    GENTLE_BREEZE = 5.5
    MODERATE_BREEZE = 7.9  # light wind
    FRESH_BREEZE = 10.7
    STRONG_BREEZE = 13.8  # strong wind
    HIGH_WIND = 17.1
    GALE = 20.7
    SEVERE_GALE = 24.4
    STORM = 28.4
    VIOLENT_STORM = 32.6
    HURRICANE = 32.7


class WeatherQuality(Enum):
    """
    Describes goodness of weather conditions.
    Higher is better (the numbers don't mean anything specific)
    """
    TORNADO = 0
    SQUALL = 1
    ASH = 2
    THUNDERSTORM = 3
    HAIL = 3.1
    SNOW = 4
    FREEZING_RAIN = 4.1
    SHOWER = 4.2
    RAIN = 5
    DRIZZLE = 6
    HAZE = 7
    FOG = 8
    DUST = 9
    MIST = 10
    SAND = 11
    SMOKE = 12
    CLOUDS = 13
    CLEAR = 14

