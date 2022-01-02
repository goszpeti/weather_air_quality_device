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
import os
import urllib.request

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from waqd.assets import get_asset_file
from waqd.base.component import Component
from waqd.base.system import RuntimeSystem
from waqd.base.logger import Logger


def is_daytime(sunrise, sunset, date_time=None):
    """
    Helper function to determine if specified time is day or night
    """
    if date_time is None:
        date_time = datetime.now()
    return sunrise < date_time.time() < sunset


@dataclass
class Weather():
    """
    This class is used to abstract from weather hosting types.
    Relies heavily on OpenWeather data structure
    """
    main: str  # condition group
    description: str  # condition detail
    date_time: datetime
    fetch_time: datetime = field(init=False)
    icon: Path
    wind_speed: float
    wind_deg: float
    sunrise: time
    sunset: time
    pressure: float
    pressure_sea_level: float  # = 1013 # default
    humidity: float
    clouds: float
    temp: float
    altitude: float

    def __post_init__(self):
        if self.main:  # only set fetch_time if it is non-empty initiallized
            self.fetch_time = datetime.now()

    def is_daytime(self):
        """
        Helper function to determine if specified time is day or night
        """
        return is_daytime(self.sunrise, self.sunset, self.date_time)


# @dataclass
# class CurrentWeather(Weather):
#     current_temp: float


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
    SNOW = 4
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


class OpenTopoData():
    QUERY = "https://api.opentopodata.org/v1/eudem25m?locations={lat},{long}"

    def __init__(self):
        super().__init__()
        self._altitude_info = {}

    def get_altitude(self, latitude: float, longitude: float) -> float:
        location_data = self._altitude_info.get("location")
        if location_data and location_data.get("lat") == latitude and location_data.get("lng") == longitude:
            return self._altitude_info.get("elevation", 0.0)

        # wait a little bit for connection
        is_connected = RuntimeSystem().wait_for_network()
        if not is_connected:
            # TODO error message
            return 0
        response_file = None
        try:
            response_file = urllib.request.urlretrieve(
                self.QUERY.format(lat=latitude, long=longitude))
        except Exception as error:
            Logger().error(f"Can't get altitude for {latitude} {longitude} : {str(error)}")

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
            self._logger.error(f"{str(city_id)} - City Id for forecast is not available.")
            self._disabled = True
        if not api_key:
            self._logger.error(f"{str(city_id)} - City Id for forecast is not available.")
            self._disabled = True

        self._current_weather: Weather = None
        self._five_day_forecast: List[DailyWeather] = []
        # TODO this should be done with a mock
        self._cw_json_file: str = ""  # for testing access
        self._fc_json_file: str = ""  # for testing access

    def get_current_weather(self) -> Optional[Weather]:
        """ Public API function to get the current weather. """
        # return if data is up-to-date in a window of 5 minutes
        current_date_time = datetime.now()
        if self._current_weather:
                if self._current_weather.fetch_time:
                    time_delta = current_date_time - self._current_weather.fetch_time
                    if time_delta.seconds < 60 * 5:  # 5 minutes
                        return self._current_weather

        current_info = self._call_ow_api(self.CURRENT_WEATHER_BY_CITY_ID_API_CMD)
        if not current_info:
            return None

        weather_info = current_info.get("weather", {})[0]
        sunrise = datetime.fromtimestamp(current_info.get("sys", {}).get("sunrise", "")).time()
        sunset = datetime.fromtimestamp(current_info.get("sys", {}).get("sunset", "")).time()
        is_day = is_daytime(sunrise, sunset)
        coord = current_info.get("coord", {})

        self._current_weather = Weather(
            weather_info.get("main"),
            weather_info.get("description"),
            datetime.now(),
            self._get_condition_icon(weather_info.get("id"), is_day),
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
                time_delta = current_date_time -self._five_day_forecast[1].fetch_time
                if time_delta.seconds < 1800:  # 0.5 h
                    return self._five_day_forecast

        [daytime_forecast_points, nighttime_forecast_points] = self.get_forecast_points()
        if not daytime_forecast_points:  # error from url call, nothing to do
            return []

        self._aggregate_forecast_points_to_days(
            daytime_forecast_points, nighttime_forecast_points)

        return self._five_day_forecast

    def get_forecast_points(self) -> Tuple[List[List[Weather]], List[List[Weather]]]:
        """ Get all forecast points, separated into day and nighttime """
        forecast = self._call_ow_api(self.FORECAST_BY_CITY_ID_API_CMD)
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
                weather_info.get("main", ""),
                weather_info.get("description", ""),
                entry_date_time,
                self._get_condition_icon(weather_info.get("id"), is_day),
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
            elif entry_date_time.time() < self._current_weather.sunrise:
                if day_idx == 0:  # separate handling for today before and after midnight
                    nighttime_forecast_points[0].append(weather_point)
                # elif day_idx == 1:  # skip todays night points that fall on next day
                #     #continue
                #     nighttime_forecast_points[1].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx-1].append(weather_point)
            else:
                if day_idx == 0:
                    if entry_date_time.time() > self._current_weather.sunset:
                        if current_datetime.time() < self._current_weather.sunrise:
                            continue  # ignore for now
                    nighttime_forecast_points[0].append(weather_point)
                else:
                    nighttime_forecast_points[day_idx].append(weather_point)
        return (daytime_forecast_points, nighttime_forecast_points)

    def _aggregate_forecast_points_to_days(self, daytime_forecast_points: List[List[Weather]], nighttime_forecast_points: List[List[Weather]]):
        """ Calculate the daily weather form the points and set self._five_day_forecast """

        # determine overall weather and wind to set the shown icon
        for day_idx in range(0, 6):
            forecast_points = daytime_forecast_points[day_idx]
            if day_idx == 0:
                current_time = datetime.now().time()
                if current_time < self._current_weather.sunrise:  # after midnight
                    forecast_points = nighttime_forecast_points[day_idx]
                elif current_time > self._current_weather.sunset:  # before midnight
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
                    overall_weather.icon = self._get_condition_icon("windy", True)
                if overall_weather.main == "Clouds":
                    overall_weather.icon = self._get_condition_icon("cloudy-windy", True)
                if overall_weather.main == "Rain":
                    overall_weather.icon = self._get_condition_icon("rain-windy", True)
                if overall_weather.main == "Snow":
                    overall_weather.icon = self._get_condition_icon("snow-windy", True)

            # init DailyWeather
            daily_weather = DailyWeather(
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

    def _call_ow_api(self, command: str) -> Dict[str, Any]:
        """ Call the REST like API of OpenWeatherMap. Return response. """
        if self._disabled:
            return {}
        # wait a little bit for connection
        is_connected = RuntimeSystem().wait_for_network()
        if not is_connected:
            # TODO error message
            return {}
        response = []
        if self._cw_json_file and command == self.CURRENT_WEATHER_BY_CITY_ID_API_CMD:
            response.append(self._cw_json_file)
        elif self._fc_json_file and command == self.FORECAST_BY_CITY_ID_API_CMD:
            response.append(self._fc_json_file)
        else:
            try:
                response = urllib.request.urlretrieve(
                    command.format(cid=self._city_id) +
                    self.API_POSTFIX.format(apikey=self._api_key))
            except Exception as error:
                self._logger.error(f"Can't get current weather for {self._city_id} : {str(error)}")

        if not response or not response or not os.path.exists(response[0]):
            return {}

        with open(response[0], encoding="utf-8") as response_json:
            return json.load(response_json)

    @staticmethod
    def _get_condition_icon(ident, is_day) -> Path:
        if is_day:
            ident = "day-" + str(ident)
        else:
            ident = "night-" + str(ident)

        file_path = get_asset_file("weather_icons", ident)

        # normalize to lower case
        if not file_path:
            file_path = get_asset_file("gui_base", "dummy.png")
        return file_path


### Currently unused code ###
# class AccuWeather():
#     location = None
#     cid = None
#     current_weather = None
#     three_day_forecast = {}
#     forecast = None  # save for later use
#     base_path = None

#     def __init__(self, location):
#         pass

#     def get_5_day_forecast(self, current_date_time=datetime.now()):
#         # http://dataservice.accuweather.com/forecasts/v1/daily/5day/187944?
#           apikey=jDNdKjSNoyqCsJpLcuhAWOJsWFcpfuo0&details=true&metric=true HTTP/1.1
#         pass

#     def get_current_weather(self):
#         # http://dataservice.accuweather.com/currentconditions/v1/187944?
#           apikey=jDNdKjSNoyqCsJpLcuhAWOJsWFcpfuo0&details=true HTTP/1.1
#         pass
