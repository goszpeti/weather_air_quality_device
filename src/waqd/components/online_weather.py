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
This file contains classes concerning online weather data.
Currently OpenWeatherMap is supported.
An own abstraction class was created to generalize the weather data.
"""

from datetime import datetime, time
import json
from re import M
import urllib.request
import requests

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from waqd.assets import get_asset_file
from waqd.base.component import Component
from waqd.base.network import Network
from waqd.base.file_logger import Logger
from waqd.settings import LAST_TEMP_C_OUTSIDE, LOCATION_ALTITUDE_M


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
    name: str  # city name TODO deprecate
    main: str  # condition  TODO deprecate or use WQ
    description: str  # condition detail TODO deprecate
    date_time: datetime # time of the point or day
    fetch_time: datetime = field(init=False)
    icon: str # icon name
    wind_speed: float  # m/s
    wind_deg: float
    sunrise: time
    sunset: time
    pressure: float # hPa
    pressure_sea_level: float  # = 1013 # default, TODO deprecate (or the other?)
    humidity: float # percent
    clouds: float  # percent cloudiness TODO deprecate
    temp: float # degC
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


class OpenMeteo(Component):
    API_FORECAST_CMD = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
    API_GEOCONDING_CMD = "https://geocoding-api.open-meteo.com/v1/search?name={query}&language={lang}"
    day_code_to_ico = {
        0: "wi-day-sunny",  # Clear sky
        1: "wi-day-overcast",
        2: "wi-day-cloudy",
        3: "wi-cloudy",
        45: "wi-day-fog", 48: "wi-fog",
        51: "wi-day-sprinkle", 53: "wi-day-sleet", 55: "wi-day-sleet",
        56: "wi-day-rain-mix", 57: "wi-day-rain-mix",
        61: "wi-day-rain", 63: "wi-day-rain", 65: "wi-day-rain",
        66: "wi-day-rain-mix", 67: "wi-day-rain-mix",  # TODO
        71: "wi-day-snow", 73: "wi-day-snow", 75: "wi-day-snow",
        77: "wi-day-snow",
        80: "wi-day-showers", 81: "wi-day-showers", 82: "wi-day-showers",
        85: "wi-day-snow", 86: "wi-day-snow",
        95: "wi-day-thunderstorm",
        96: "wi-day-hail", 99: "wi-day-hail"  # TODO hail
        }
    night_code_to_ico = {
        0: "wi-night-clear",
        1: "wi-night-alt-partly-cloudy",
        2: "wi-night-alt-cloudy",
        3: "wi-night-alt-cloudy",
        45: "wi-night-fog", 48: "wi-fog",
        51: "wi-night-alt-sprinkle", 53: "wi-night-alt-sleet", 55: "wi-night-alt-sleet",
        56: "wi-night-alt-rain-mix", 57: "wi-night-alt-rain-mix",
        61: "wi-night-alt-rain", 63: "wi-night-alt-rain", 65: "wi-night-alt-rain",
        66: "wi-night-alt-rain-mix", 67: "wi-day-rain-mix",  # TODO
        71: "wi-night-alt-snow", 73: "wi-night-alt-snow", 75: "wi-night-alt-snow",
        77: "wi-night-alt-snow",
        80: "wi-night-alt-showers", 81: "wi-night-alt-showers", 82: "wi-day-showers",
        85: "wi-night-alt-snow", 86: "wi-night-alt-snow",
        95: "wi-night-alt-snow-thunderstorm",
        96: "wi-night-alt-snow-thunderstorm", 99: "wi-night-alt-snow-thunderstorm"  # TODO hail
         }
    condition_map = {  # for bg image - TODO use WeatherQuality
        0: "clear", # add table for this
        1: "clouds", 2: "clouds", 3: "clouds",
        45: "fog", 48: "fog",
        51: "drizzle", 53: "drizzle", 55: "drizzle",
        56: "drizzle", 57: "drizzle", # TODO get image
        61: "rain", 63: "rain", 65: "rain",
        66: "rain", 67: "rain", # TODO
        71: "snow", 73: "snow", 75: "snow",
        77: "snow",
        80: "rain", 81: "rain", 82: "rain", # TOODO showers
        85: "snow", 86: "snow",
        95: "thunderstorm", 
        96: "thunderstorm", 99: "thunderstorm"  # TODO hail
    }
        # 1, 2, 3	Mainly clear, partly cloudy, and overcast
        # 45, 48	Fog and depositing rime fog
        # 51, 53, 55	Drizzle: Light, moderate, and dense intensity
        # 56, 57	Freezing Drizzle: Light and dense intensity
        # 61, 63, 65	Rain: Slight, moderate and heavy intensity
        # 66, 67	Freezing Rain: Light and heavy intensity
        # 71, 73, 75	Snow fall: Slight, moderate, and heavy intensity
        # 77	Snow grains
        # 80, 81, 82	Rain showers: Slight, moderate, and violent
        # 85, 86	Snow showers slight and heavy
        # 95 * Thunderstorm: Slight or moderate
        # 96, 99 * Thunderstorm with slight and heavy hail
    
    def __init__(self, longitude=0.0, latitude=0.0):
        super().__init__()
        self._longitude = longitude
        self._latitude = latitude
        self._current_weather: Optional[Weather] = None
        self._five_day_forecast: List[DailyWeather] = []
        self._ready = True
        self.daytime_forecast_points = []
        self.nighttime_forecast_points = []

    def find_location_candidates(self, query: str, lang="en") -> List[Location]:
        """ """
        data = self._call_api(self.API_GEOCONDING_CMD, query=query, lang=lang)
        locations = []
        for result in data.get("results", []):
            locations.append(
                Location(
                    result.get("name", ""),
                    result.get("country", ""),
                    result.get("admin1", ""),
                    result.get("admin2", ""),
                    result.get("postcodes", []),
                    result.get("elevation", 0),
                    result.get("latitude", 0),
                    result.get("longitude", 0),
            ))
        return locations

    def get_current_weather(self) -> Optional[Weather]:
        """ Public API function to get the current weather. """
        # return if data is up-to-date in a window of 5 minutes
        current_date_time = datetime.now()
        if self._current_weather:
            if self._current_weather.fetch_time:
                time_delta = current_date_time - self._current_weather.fetch_time
                if time_delta.seconds > 60 * 5:  # 5 minutes
                    self._get_daily_weathers()
        else:
            self._get_daily_weathers()
        return self._current_weather

    def get_5_day_forecast(self) -> List[DailyWeather]:
        current_date_time = datetime.now()
        if len(self._five_day_forecast) > 1:
            if self._five_day_forecast[1].fetch_time:
                time_delta = current_date_time - self._five_day_forecast[1].fetch_time
                if time_delta.seconds > 1800:  # 0.5 h
                    self._get_hourly_weather()
                    self._get_daily_weathers()
        return self._five_day_forecast
        
    def _get_daily_weathers(self):
        response = self._call_api(
            self.API_FORECAST_CMD +
            "&daily=weathercode,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum," + 
            "rain_sum,showers_sum,snowfall_sum,precipitation_hours,windspeed_10m_max," +
            "winddirection_10m_dominant&current_weather=true&windspeed_unit=ms&timezone=auto",
            latitude=self._latitude, longitude=self._longitude)
        if not response:
            return None

        current_weather = response.get("current_weather", {})
        daily = response.get("daily", {})
        for i in range(len(daily)):
            sunrise = datetime.fromisoformat(daily.get("sunrise", [])[i]).time()
            sunset = datetime.fromisoformat(daily.get("sunset", [])[i]).time()
            is_day = is_daytime(sunrise, sunset)
            daily_weather = DailyWeather(
                "",
                "",
                "",
                datetime.fromisoformat(daily.get("time", [])[i]),
                Weather.get_icon(daily.get("weathercode", [])[i], is_day),
                daily.get("windspeed_10m_max", [])[i],
                daily.get("winddirection_10m_dominant", [])[i],
                sunrise, sunset,
                0,0,0,0,
                0, response.get("elevation", [])[i]
            )
            daily_weather.temp_min = daily.get("temperature_2m_min", [])[i]
            daily_weather.temp_max = daily.get("temperature_2m_max", [])[i]
            # TODO
            daily_weather.temp_night_min = daily.get("temperature_2m_min", [])[i]
            daily_weather.temp_night_max = daily.get("temperature_2m_min", [])[i]
            self._five_day_forecast.append(daily_weather)
        # current weather
        sunrise = self._five_day_forecast[0].sunrise
        sunset = self._five_day_forecast[0].sunset
        is_day = is_daytime(sunrise, sunset)
        self._current_weather = Weather(
            "",  # TODO remove
            current_weather.get("weathercode", 0),
            "",
            #current_weather.get("description"), # TODO detail
            datetime.now(),
            Weather.get_icon(current_weather.get("weathercode", 0), is_day),
            response.get("windspeed", 0.0) * 3.6, # km/h -> m/s
            response.get("winddirection", 0.0),
            sunrise, sunset,
            1000.0, # no data
            1000.0,  # no data,
            0, # TODO get from hourly forecast
            0.0,
            current_weather.get("temperature", 0.0),
            response.get("elevation", 0)
        )

        return self._current_weather

    def _get_hourly_weather(self):
        response = self._call_api(
            self.API_FORECAST_CMD +
            "&hourly=temperature_2m,relativehumidity_2m,precipitation,cloudcover,weathercode,pressure_msl," +
            "surface_pressure,windspeed_10m,winddirection_10m&windspeed_unit=ms",
            latitude=self._latitude, longitude=self._longitude)
        if not response:
            return None
        # now aggregate the data - every 3 hours for 5 days and populate daily_forecast_points
        daytime_forecast_points: List[List[Weather]] = [[] for i in range(7)]
        nighttime_forecast_points: List[List[Weather]] = [[] for i in range(7)]
        # we need sunrise and sunset info from current weather to know what day and night is
        current_weather = self.get_current_weather()
        if not current_weather:
            return ([], [])
        current_datetime = datetime.now()
        for i in range(len(response.get("time", []))):
            # utc to local time
            entry_date_time = datetime.fromtimestamp(response.get("time", [])[i])
            time_delta = entry_date_time.date() - current_datetime.date()
            day_idx = time_delta.days
            if day_idx > 5 or day_idx < 0:
                continue
            is_day = is_daytime(current_weather.sunrise, current_weather.sunset, entry_date_time)
            weather_point = Weather(
                "",  # no name necessary
                "",
                "",
                entry_date_time,
                Weather.get_icon(response.get("weathercode", ""), is_day),
                response.get("windspeed_10m", [])[i],
                response.get("winddirection_10m", [])[i],
                current_weather.sunrise, current_weather.sunset, # TODO use day
                response.get("surface_pressure", [])[i],
                response.get("pressure_msl", [])[i],
                response.get("relativehumidity_2m", [])[i],
                response.get("relativehumidity_2m", [])[i],
                response.get("temperature_2m", [])[i],
                current_weather.altitude
            )

            if is_day:
                daytime_forecast_points[day_idx].append(weather_point)
            # this counts as night of the previous day
            elif entry_date_time.time() < current_weather.sunrise:
                if day_idx == 0:  # separate handling for today before and after midnight
                    nighttime_forecast_points[0].append(weather_point)
                # elif day_idx == 1:  # skip todays night points that fall on next day
                #     #continue
                #     nighttime_forecast_points[1].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx-1].append(weather_point)
            else:
                if day_idx == 0:
                    if entry_date_time.time() > current_weather.sunset:
                        if current_datetime.time() < current_weather.sunrise:
                            continue  # ignore for now
                    nighttime_forecast_points[0].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx].append(weather_point)
        self.daytime_forecast_points = daytime_forecast_points
        self.nighttime_forecast_points = nighttime_forecast_points
        # calculate min/max night and daytime temps
        self._set_min_max_temps(daytime_forecast_points, nighttime_forecast_points)

    def _set_min_max_temps(self, daytime_forecast_points: List[List[Weather]], nighttime_forecast_points: List[List[Weather]]):
        for day_idx, forecast_points in enumerate(daytime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                if len(self._five_day_forecast) > day_idx:
                    self._five_day_forecast[day_idx].temp_max = float("inf")
                    self._five_day_forecast[day_idx].temp_min = -float("inf")
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_min = min_temp

        for day_idx, forecast_points in enumerate(nighttime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                if len(self._five_day_forecast) > day_idx:
                    self._five_day_forecast[day_idx].temp_night_max = float("inf")
                    self._five_day_forecast[day_idx].temp_night_min = -float("inf")
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_min = min_temp



    def _call_api(self, command: str, **kwargs) -> Dict[str, Any]:
        """ Call the REST like API of OpenWeatherMap. Return response. """
        if self._disabled:
            return {}
        # wait a little bit for connection
        is_connected = Network().wait_for_internet()
        if not is_connected:
            self._logger.error("OpenMeteo: Timeout while wating for network connection")
            return {}
        try:
            command = command.format(**kwargs)
            response = requests.get(command, timeout=5)
            if response.ok:
                return response.json()
        except Exception as error:
            self._logger.error(f"OpenMeteo: Can't get data: {str(error)}")
        return {}


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


class OpenWeatherMap(Component):
    """
    Interface to data from OpenWeatherMap, to get Current weather or 5 day forecast data.
    Only needs a free API key.
    """

    CURRENT_WEATHER_BY_CITY_ID_API_CMD = \
        "http://api.openweathermap.org/data/2.5/weather?id={cid}"
    FORECAST_BY_CITY_ID_API_CMD = \
        "http://api.openweathermap.org/data/2.5/forecast?id={cid}"
    API_POSTFIX = "&units=metric&APPID={apikey}"

    def __init__(self, city_id, api_key):
        super().__init__()
        self._city_id = city_id  # use id, name is ambiguous
        self._api_key = api_key
        self._topo_data = OpenTopoData()

        if not self._city_id:
            self._logger.error(f"OpenWeatherMap: {str(city_id)} - City Id for forecast is not available.")
            self._disabled = True
        if not api_key:
            self._logger.error("OpenWeatherMap: API Key for forecast is not available.")
            self._disabled = True

        self._current_weather: Optional[Weather] = None
        self._five_day_forecast: List[DailyWeather] = []
        self.daytime_forecast_points = []
        self.nighttime_forecast_points = []
        # query data ini init, so it doesn't run in the GUI thread
        self.get_5_day_forecast()
        self._ready = True

    def get_current_weather(self) -> Optional[Weather]:
        """ Public API function to get the current weather. """
        # return if data is up-to-date in a window of 5 minutes
        current_date_time = datetime.now()
        if self._current_weather:
            if self._current_weather.fetch_time:
                time_delta = current_date_time - self._current_weather.fetch_time
                if time_delta.seconds < 60 * 5:  # 5 minutes
                    return self._current_weather

        current_info = self._call_api(self.CURRENT_WEATHER_BY_CITY_ID_API_CMD)
        if not current_info:
            return None

        weather_info = current_info.get("weather", {})[0]
        sunrise = datetime.fromtimestamp(current_info.get("sys", {}).get("sunrise", "")).time()
        sunset = datetime.fromtimestamp(current_info.get("sys", {}).get("sunset", "")).time()
        is_day = is_daytime(sunrise, sunset)
        coord = current_info.get("coord", {})

        self._current_weather = Weather(
            current_info.get("name", ""),
            weather_info.get("main"),
            weather_info.get("description"),
            datetime.now(),
            self._get_icon_name(weather_info.get("id"), is_day),
            current_info.get("wind", {}).get("speed", 0.0),
            current_info.get("wind", {}).get("deg", 0.0),
            sunrise, sunset,
            current_info.get("main", {}).get("pressure", 1000.0),
            current_info.get("main", {}).get("sea_level", 1000.0),
            current_info.get("main", {}).get("humidity", 0.0),
            current_info.get("clouds", {}).get("all", 0.0),
            current_info.get("main", {}).get("temp", 0.0),
            self._topo_data.get_altitude(coord.get("lat", 0.0), coord.get("lon", 0.0))
        )
        return self._current_weather

    def get_5_day_forecast(self) -> List[DailyWeather]:
        """ Public forecast API function. """
        # return if data is up-to-date in a window half an hour
        current_date_time = datetime.now()
        if len(self._five_day_forecast) > 1:
            if self._five_day_forecast[1].fetch_time:
                time_delta = current_date_time - self._five_day_forecast[1].fetch_time
                if time_delta.seconds < 1800:  # 0.5 h
                    return self._five_day_forecast

        [self.daytime_forecast_points, self.nighttime_forecast_points] = self._get_forecast_points()
        if not self.daytime_forecast_points:  # error from url call, nothing to do
            return []
        current_weather = self.get_current_weather()
        if not current_weather:
            return []
        self._aggregate_forecast_points_to_days(
            self.daytime_forecast_points, self.nighttime_forecast_points, current_weather)

        return self._five_day_forecast

    def _get_forecast_points(self) -> Tuple[List[List[Weather]], List[List[Weather]]]:
        """ Get all forecast points, separated into day and nighttime """
        forecast = self._call_api(self.FORECAST_BY_CITY_ID_API_CMD)
        if not forecast:  # error from call, nothing to do
            return ([], [])

        # now aggregate the data - every 3 hours for 5 days and populate daily_forecast_points
        daytime_forecast_points: List[List[Weather]] = [[] for i in range(7)]
        nighttime_forecast_points: List[List[Weather]] = [[] for i in range(7)]
        # we need sunrise and sunset info from current weather to know what day and night is
        current_weather = self.get_current_weather()
        if not current_weather:
            return ([], [])
        current_datetime = datetime.now()
        for measurement_point in forecast.get("list", []):
            # utc to local time
            entry_date_time = datetime.fromtimestamp(measurement_point.get("dt"))
            time_delta = entry_date_time.date() - current_datetime.date()
            day_idx = time_delta.days
            if day_idx > 5 or day_idx < 0:
                continue
            is_day = is_daytime(current_weather.sunrise, current_weather.sunset, entry_date_time)
            # api defines only one point, no defense needed - and if is, the functionilty will not work either
            weather_info: Dict[str, Any] = measurement_point.get("weather")[0]
            if not weather_info:
                continue
            weather_point = Weather(
                "",  # no name necessary
                weather_info.get("main", ""),
                weather_info.get("description", ""),
                entry_date_time,
                self._get_icon_name(weather_info.get("id", ""), is_day),
                measurement_point.get("wind").get("speed"),
                measurement_point.get("wind").get("deg"),
                current_weather.sunrise, current_weather.sunset,
                0, 0, 0,  # currently unused
                measurement_point.get("clouds").get("all"),
                measurement_point.get("main").get("temp"),
                current_weather.altitude
            )

            if is_day:
                daytime_forecast_points[day_idx].append(weather_point)
            # this counts as night of the previous day
            elif entry_date_time.time() < current_weather.sunrise:
                if day_idx == 0:  # separate handling for today before and after midnight
                    nighttime_forecast_points[0].append(weather_point)
                # elif day_idx == 1:  # skip todays night points that fall on next day
                #     #continue
                #     nighttime_forecast_points[1].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx-1].append(weather_point)
            else:
                if day_idx == 0:
                    if entry_date_time.time() > current_weather.sunset:
                        if current_datetime.time() < current_weather.sunrise:
                            continue  # ignore for now
                    nighttime_forecast_points[0].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx].append(weather_point)
        return (daytime_forecast_points, nighttime_forecast_points)

    def _aggregate_forecast_points_to_days(self, daytime_forecast_points: List[List[Weather]],
                                           nighttime_forecast_points: List[List[Weather]],
                                           current_weather: Weather):
        """ Calculate the daily weather form the points and set self._five_day_forecast """
        self._five_day_forecast = []
        # determine overall weather and wind to set the shown icon
        for day_idx in range(0, 6):
            forecast_points = daytime_forecast_points[day_idx]
            if day_idx == 0:
                current_time = datetime.now().time()
                if current_time < current_weather.sunrise:  # after midnight
                    forecast_points = nighttime_forecast_points[day_idx]
                elif current_time > current_weather.sunset:  # before midnight
                    forecast_points = nighttime_forecast_points[day_idx]
                    if not forecast_points:
                        forecast_points = nighttime_forecast_points[day_idx + 1]
                if not forecast_points:  # before sunset
                    forecast_points = nighttime_forecast_points[day_idx]

            overall_weather = OpenWeatherMap._determine_daily_overall_weather(forecast_points)

            if not overall_weather:  # defense for empty info
                continue

            max_wind_speed = max([point.wind_speed for point in forecast_points])
            # enhance icon with wind information - we already have strong wind and onwards
            # as an extra condition
            if max_wind_speed > BeaufortScale.FRESH_BREEZE.value:
                if overall_weather.main == "Clear":
                    overall_weather.icon = self._get_icon_name("windy", True)
                if overall_weather.main == "Clouds":
                    overall_weather.icon = self._get_icon_name("cloudy-windy", True)
                if overall_weather.main == "Rain":
                    overall_weather.icon = self._get_icon_name("rain-windy", True)
                if overall_weather.main == "Snow":
                    overall_weather.icon = self._get_icon_name("snow-windy", True)

            # init DailyWeather
            daily_weather = DailyWeather(
                current_weather.name,
                overall_weather.main,
                overall_weather.description,
                overall_weather.date_time,
                overall_weather.icon,
                max_wind_speed,
                overall_weather.wind_deg,
                overall_weather.sunrise, overall_weather.sunset,
                0, 0, 0,  # currently unused
                overall_weather.clouds,
                float(overall_weather.temp),
                overall_weather.altitude
            )
            self._five_day_forecast.append(daily_weather)
        # calculate min/max night and daytime temps
        self._set_min_max_temps(daytime_forecast_points, nighttime_forecast_points)

    def _set_min_max_temps(self, daytime_forecast_points: List[List[Weather]], nighttime_forecast_points: List[List[Weather]]):
        for day_idx, forecast_points in enumerate(daytime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                if len(self._five_day_forecast) > day_idx:
                    self._five_day_forecast[day_idx].temp_max = float("inf")
                    self._five_day_forecast[day_idx].temp_min = -float("inf")
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_min = min_temp

        for day_idx, forecast_points in enumerate(nighttime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                if len(self._five_day_forecast) > day_idx:
                    self._five_day_forecast[day_idx].temp_night_max = float("inf")
                    self._five_day_forecast[day_idx].temp_night_min = -float("inf")
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_min = min_temp

    @staticmethod
    def _determine_daily_overall_weather(measurement_points: List[Weather]):
        """
        Get the weather to be shown on the forecast icon.
        The strategy is to first sort after the main category, e.g. rain, snow.
        All the categories are listed in the WeatherQuality class and are ordered from bad to good.
        In case there are multiple categories, first try determine the most numerous one.
        If there are equal in count, take the one with the most bad.

        return : the measurement point (Weather) representing the daily weather(main and description)
        """

        if not measurement_points:
            return None

        # first try look in main categories and get enumerate all of them
        main_count_dict = {}
        for measurement_point in measurement_points:
            if measurement_point.main not in main_count_dict:  # filter empty
                main_count_dict.update({measurement_point.main: 1})
                continue
            main_count_dict[measurement_point.main] += 1

        if not main_count_dict:  # something went wrong, no categories were found
            return None

        # dominant_categories can be a list or a single element
        max_count = max(main_count_dict.values())
        max_indices = [i for i, x in enumerate(
            main_count_dict.values()) if x == max_count]
        dominant_categories = [list(main_count_dict)[i]
                               for i in max_indices]

        # there are multiple candidates
        if isinstance(dominant_categories, list):
            # get the worst case - we want to know, if it snows in the middle of the day
            # init with max value
            worst_idx = max(list(map(lambda c: c.value, WeatherQuality)))
            for category in dominant_categories:
                # enum is uppercase
                category_quality = WeatherQuality[category.upper()]
                worst_idx = min(worst_idx, category_quality.value)
            result_category = WeatherQuality(worst_idx)
        else:  # one element
            result_category = dominant_categories

        # get the most prevalent detailed description
        description = OpenWeatherMap._find_dominant_detailed_weather(
            measurement_points, result_category)

        # only need one
        return [point for point in measurement_points if point.description == description][0]

    @staticmethod
    def _find_dominant_detailed_weather(measurement_points: List[Weather], category: WeatherQuality):
        """ Tries to find the best matching detailed weather for the day """

        # count all detailed conditions with the selected main category
        detail_count_dict = {}
        for point in measurement_points:
            if category.name in point.main.upper():  # and point.description:
                if not point.description in detail_count_dict:
                    detail_count_dict[point.description] = 1
                    continue
                detail_count_dict[point.description] += 1
        max_count = max(detail_count_dict.values())
        max_indices = [i for i, x in enumerate(detail_count_dict.values()) if x == max_count]
        dominant_categories = [list(detail_count_dict)[i]
                               for i in max_indices]

        # determine winner from position
        # 11, 14 and 17 hours TODO this is crap
        if isinstance(dominant_categories, list):
            # if len(dominant_categories) == 1:
            return dominant_categories[0]
            # return measurement_points[-1].description  # get last element
        return dominant_categories

    def _call_api(self, command: str) -> Dict[str, Any]:
        """ Call the REST like API of OpenWeatherMap. Return response. """
        if self._disabled:
            return {}
        # wait a little bit for connection
        is_connected = Network().wait_for_internet()
        if not is_connected:
            self._logger.error("OpenWeatherMap: Timeout while wating for network connection")
            return {}
        try:
            response = requests.get(command.format(cid=self._city_id) +
                                    self.API_POSTFIX.format(apikey=self._api_key), timeout=5)
            if response.ok:
                return response.json()
        except Exception as error:
            self._logger.error(
                f"OpenWeatherMap: Can't get current weather for {self._city_id} : {str(error)}")
        return {}
    @staticmethod
    def _get_icon_name(ident="", is_day=False):
        """
        Helper function to get icon from condition.
        If ident is empty, it uses it's own id to determine the condition.
        """
        if is_day:
            ident = "day-" + str(ident)
        else:
            ident = "night-" + str(ident)
        return ident
