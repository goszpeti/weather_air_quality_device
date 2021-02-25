"""
This file contains classes concerning online weather data.
Currently OpenWeatherMap is supported.
An own abstraction class was created to generalize the weather data.
"""

import datetime
import json
import os
import urllib.request
from enum import Enum
from pathlib import Path

from piweather.base.components import Component
from piweather.resources import get_rsc_file
from piweather.settings import LOCATION, OW_API_KEY, OW_CITY_IDS


class Weather():
    """
    This class is used to abstract from weather hosting types.
    Currently in progress, relies heavily on OpenWeather data structure
    """

    def __init__(self, main: str, description: str, date_time: datetime.datetime = None):
        self.main = main  # condition group
        self.description = description  # condition detail
        self.date_time = date_time
        if self.main:  # only set fetch_time if it is non-empty initiallized
            self.fetch_time = datetime.datetime.now()
        else:
            self.fetch_time = None
        self.icon: Path = None
        self.wind_speed = None
        self.wind_deg = None
        self.temp = None  # only current
        self.temp_min = None  # only daily
        self.temp_max = None  # only daily
        self.temp_night_min = None  # only daily
        self.temp_night_max = None  # only daily
        self.sunrise: datetime.time = None
        self.sunset: datetime.time = None
        self.pressure = None
        self.humidity = None
        self.clouds = None
        self.current_temp = None

    def update(self, weather_obj: "Weather"):
        """ overwrites the internal values with another weather object """
        if weather_obj:
            for attr, value in weather_obj.__dict__.items():
                if value:
                    setattr(self, attr, value)

    def is_daytime(self, date_time=None, sunrise=None, sunset=None):
        """
        Helper function to determine if specified time is day or night
        """
        if date_time is None:
            date_time = datetime.datetime.now()
        if sunrise is None:
            sunrise = self.sunrise
        if sunset is None:
            sunset = self.sunset

        return sunrise < date_time.time() < sunset


class BeaufortScale(Enum):
    """ Wind severity with max m/s """
    calm = 0.5
    light_air = 1.5
    light_breeze = 3.3
    gentle_breeze = 5.5
    moderate_breeze = 7.9  # light wind
    fresh_breeze = 10.7
    strong_breeze = 13.8  # strong wind
    high_wind = 17.1
    gale = 20.7
    severe_gale = 24.4
    storm = 28.4
    violent_storm = 32.6
    hurricane = 32.7


class OpenWeatherMap(Component):
    """
    Interface to data from OpenWeatherMap, to get Current weather or 5 day forecast data.
    Only needs a free API key.
    """

    class WeatherQuality(Enum):
        """
        Describes goodness of weather conditions.
        Higher is better (the numbers don't mean anything specific)
        """
        Tornado = 0
        Squall = 1
        Ash = 2
        Thunderstorm = 3
        Snow = 4
        Rain = 5
        Drizzle = 6
        Haze = 7
        Fog = 8
        Dust = 9
        Mist = 10
        Sand = 11
        Smoke = 12
        Clouds = 13
        Clear = 14

    CURRENT_WEATHER_BY_CITY_ID_API_CMD = \
        "http://api.openweathermap.org/data/2.5/weather?id={cid}"
    FORECAST_BY_CITY_ID_API_CMD = \
        "http://api.openweathermap.org/data/2.5/forecast?id={cid}"
    API_POSTFIX = "&units=metric&APPID={apikey}"

    def __init__(self, settings):
        super().__init__(settings=settings)
        self._city_id: str = None  # use id, name is ambiguous
        self._current_weather: Weather = None
        # 3 hours before midnight there won't be a current day, so it gets 6 days
        self._five_day_forecast = [Weather("", "", "") for i in range(6)]
        # TODO this should be done with a mock
        self._cw_json_file: str = None  # for testing access
        self._fc_json_file: str = None  # for testing access

    def get_current_weather(self) -> Weather:
        """ Public API function to get the current weather. """
        current_weather = self._call_ow_api(self.CURRENT_WEATHER_BY_CITY_ID_API_CMD)
        if not current_weather:
            return None
        weather = current_weather.get("weather")[0]
        self._current_weather = Weather(
            weather.get("main"), weather.get("description"), datetime.datetime.now())
        self._current_weather.current_temp = current_weather.get("main").get("temp")
        self._current_weather.pressure = current_weather.get("main").get("pressure")
        self._current_weather.humidity = current_weather.get("main").get("humidity")
        self._current_weather.clouds = current_weather.get("clouds").get("all")
        self._current_weather.wind_deg = current_weather.get("wind").get("deg")
        self._current_weather.wind_speed = current_weather.get("wind").get("speed")
        self._current_weather.sunrise = datetime.datetime.fromtimestamp(
            current_weather.get("sys").get("sunrise")).time()
        self._current_weather.sunset = datetime.datetime.fromtimestamp(
            current_weather.get("sys").get("sunset")).time()
        is_day = self._current_weather.is_daytime()
        self._current_weather.icon = self._get_condition_icon(weather.get("id"), is_day)
        return self._current_weather

    def get_5_day_forecast(self) -> [Weather]:
        """ Public forecast API function. """
        # return if data is up-to-date in a window half an hour
        current_date_time = datetime.datetime.now()
        if len(self._five_day_forecast) > 1:
            if self._five_day_forecast[1].fetch_time:
                time_delta = self._five_day_forecast[1].fetch_time - \
                    current_date_time
                if 0 < time_delta.seconds < 1800:  # 0.5 h
                    return self._five_day_forecast

        [daytime_forecast_points, nighttime_forecast_points] = self._get_forecast_points()
        if not daytime_forecast_points:  # error from url call, nothing to do
            return None

        self._aggregate_forecast_points_to_days(
            daytime_forecast_points, nighttime_forecast_points)

        return self._five_day_forecast

    def _get_forecast_points(self) -> [[Weather], [Weather]]:
        """ Get all forecast points, separated into day and nighttime """
        forecast = self._call_ow_api(self.FORECAST_BY_CITY_ID_API_CMD)
        if not forecast:  # error from call, nothing to do
            return [None, None]

        # now aggregate the data - every 3 hours for 5 days and populate daily_forecast_points
        daytime_forecast_points = [[] for i in range(6)]
        nighttime_forecast_points = [[] for i in range(6)]
        # we need sunrise and sunset info from current weather to know what day and night is
        self.get_current_weather()
        current_datetime = datetime.datetime.now()
        for measurement_point in forecast.get("list"):
            # utc to local time
            entry_date_time = datetime.datetime.fromtimestamp(measurement_point.get("dt"))
            time_delta = entry_date_time.date() - current_datetime.date()
            day_idx = time_delta.days

            # api defines only one point, no defense needed
            weather_info = measurement_point.get("weather")[0]

            weather_point = Weather(weather_info.get("main"),
                                    weather_info.get("description"), entry_date_time)

            is_day = self._current_weather.is_daytime(entry_date_time)
            weather_point.icon = self._get_condition_icon(weather_info.get("id"), is_day)
            weather_point.temp = measurement_point.get("main").get("temp")
            weather_point.clouds = measurement_point.get("clouds").get("all")
            weather_point.wind_deg = measurement_point.get("wind").get("deg")
            weather_point.wind_speed = measurement_point.get(
                "wind").get("speed")

            if is_day:
                daytime_forecast_points[day_idx].append(weather_point)
            # this counts as night of the previous day
            elif entry_date_time.time() < self._current_weather.sunrise:
                if day_idx == 0:  # separate handling for today before and after midnight
                    nighttime_forecast_points[day_idx].append(weather_point)
                elif day_idx == 1:  # todays night points that fall on next day
                    nighttime_forecast_points[0].append(weather_point)
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
        return [daytime_forecast_points, nighttime_forecast_points]

    def _aggregate_forecast_points_to_days(self, daytime_forecast_points, nighttime_forecast_points):
        """ Calculate the daily weather form the points and set self._five_day_forecast """
        # calculate min/max night and daytime temps
        self._set_min_max_temps(daytime_forecast_points, nighttime_forecast_points)

        # determine overall weather and wind to set the shown icon
        for day_idx in range(0, 6):
            forecast_points = daytime_forecast_points[day_idx]
            if day_idx == 0:
                current_time = datetime.datetime.now().time()
                if current_time < self._current_weather.sunrise:  # after midnight
                    forecast_points = nighttime_forecast_points[day_idx]
                elif current_time > self._current_weather.sunset:  # before midnight
                    forecast_points = nighttime_forecast_points[day_idx]
                    if not forecast_points:
                        forecast_points = nighttime_forecast_points[day_idx + 1]
                if not forecast_points:  # before sunset
                    forecast_points = nighttime_forecast_points[day_idx]

            daily_weather = OpenWeatherMap._determine_daily_overall_weather(forecast_points)

            if not daily_weather:  # defense for empty info
                continue
            self._five_day_forecast[day_idx].main = daily_weather.main
            self._five_day_forecast[day_idx].description = daily_weather.description

            max_wind_speed = max([point.wind_speed for point in forecast_points])
            self._five_day_forecast[day_idx].wind_speed = max_wind_speed
            # enhance icon with wind information - we already have strong wind and onwards
            # as an extra condition
            if max_wind_speed > BeaufortScale.fresh_breeze.value:
                if daily_weather.main == "Clear":
                    daily_weather.icon = self._get_condition_icon("windy", True)
                if daily_weather.main == "Clouds":
                    daily_weather.icon = self._get_condition_icon("cloudy-windy", True)
                if daily_weather.main == "Rain":
                    daily_weather.icon = self._get_condition_icon("rain-windy", True)
                if daily_weather.main == "Snow":
                    daily_weather.icon = self._get_condition_icon("snow-windy", True)
            self._five_day_forecast[day_idx].icon = daily_weather.icon

    def _set_min_max_temps(self, daytime_forecast_points, nighttime_forecast_points):
        for [day_idx, forecast_points] in enumerate(daytime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_min = min_temp

        for [day_idx, forecast_points] in enumerate(nighttime_forecast_points):
            if not forecast_points:  # empty 0. day before midnight
                continue
            max_temp = max([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_max = max_temp
            min_temp = min([point.temp for point in forecast_points])
            self._five_day_forecast[day_idx].temp_night_min = min_temp

    @staticmethod
    def _determine_daily_overall_weather(measurement_points: Weather):
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
            worst_idx = max(list(map(lambda c: c.value, OpenWeatherMap.WeatherQuality)))
            for category in dominant_categories:
                category_quality = OpenWeatherMap.WeatherQuality[category]
                worst_idx = min(worst_idx, category_quality.value)
            result_category = OpenWeatherMap.WeatherQuality(worst_idx)
        else:  # one element
            result_category = dominant_categories

        # get the most prevalent detailed description
        description = OpenWeatherMap._find_dominant_detailed_weather(
            measurement_points, result_category)

        # only need one
        return [point for point in measurement_points if point.description == description][0]

    @staticmethod
    def _find_dominant_detailed_weather(measurement_points: [Weather], category: WeatherQuality = None):
        """ Tries to find the best matching detailed weather for the day """

        # count all detailed conditions with the selected main category
        detail_count_dict = {}
        for point in measurement_points:
            if category.name in point.main:  # and point.description:
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
            return measurement_points[-1].description  # get last element
        return dominant_categories

    def _call_ow_api(self, command: str) -> dict:
        """ Call the REST like API of OpenWeatherMap. Return response. """
        # get location
        location = self._settings.get(LOCATION)
        if not location:
            self._logger.warning("No location given for forecast.")

        # get city id from settings
        self._city_id = self._settings.get(OW_CITY_IDS).get(location)
        if not self._city_id:
            self._logger.error(
                "%s - City Id for forecast is not available.", location)

        response = []
        if self._cw_json_file and command == self.CURRENT_WEATHER_BY_CITY_ID_API_CMD:
            response.append(self._cw_json_file)
        elif self._fc_json_file and command == self.FORECAST_BY_CITY_ID_API_CMD:
            response.append(self._fc_json_file)
        else:
            try:
                response = urllib.request.urlretrieve(
                    command.format(cid=self._city_id) +
                    self.API_POSTFIX.format(apikey=self._settings.get(OW_API_KEY)))
            except Exception as error:
                self._logger.error("Can't get current weather for %s : %s",
                                   location, str(error))

        if not response or not response or not os.path.exists(response[0]):
            return None

        with open(response[0]) as response_json:
            return json.load(response_json)

    @staticmethod
    def _get_condition_icon(ident, is_day):
        if is_day:
            ident = "day-" + str(ident)
        else:
            ident = "night-" + str(ident)

        file_path = get_rsc_file("weather_icons", ident)

        # normalize to lower case
        if not file_path:
            file_path = get_rsc_file("gui_base", "dummy.png")
        return file_path
