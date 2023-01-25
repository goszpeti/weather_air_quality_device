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

from datetime import datetime, timedelta
import requests

from typing import Dict, List, Optional, Any

from waqd.base.component import Component
from waqd.base.network import Network

from .base_types import Location, Weather, DailyWeather, is_daytime

from .icon_mapping import om_condition_map, om_day_code_to_ico, om_night_code_to_ico

class OpenMeteo(Component):
    API_FORECAST_CMD = "https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
    API_GEOCONDING_CMD = "https://geocoding-api.open-meteo.com/v1/search?name={query}&language={lang}"

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
        self._fetch_weather()
        return self._current_weather

    def get_5_day_forecast(self) -> List[DailyWeather]:
        self._fetch_weather()
        return self._five_day_forecast

    def _fetch_weather(self):
        # return if data is up-to-date in a window of 5 minutes
        current_date_time = datetime.now()
        if self._current_weather and self._current_weather.fetch_time:
            time_delta = current_date_time - self._current_weather.fetch_time
            if time_delta.seconds < 60 * 5:  # 5 minutes
                return
        self._fetch_daily_weather()
        self._fetch_hourly_weather()
        # add pressure, humidty and clouds to cw
        self._complete_daily_weather()

    def _fetch_daily_weather(self):
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
        for i in range(len(daily.get("time", []))):
            sunrise = datetime.fromisoformat(daily.get("sunrise", [])[i]).time()
            sunset = datetime.fromisoformat(daily.get("sunset", [])[i]).time()
            is_day = is_daytime(sunrise, sunset)
            daily_weather = DailyWeather(
                "",
                self._get_main_category(daily.get("weathercode", [])[i]),
                "",
                datetime.fromisoformat(daily.get("time", [])[i]),
                self._get_icon_name(daily.get("weathercode", [])[i], is_day),
                daily.get("windspeed_10m_max", [])[i],
                daily.get("winddirection_10m_dominant", [])[i],
                sunrise, sunset,
                0, 0, 0, 0,
                0, response.get("elevation", [])
            )
            daily_weather.temp_min = daily.get("temperature_2m_min", [])[i]
            daily_weather.temp_max = daily.get("temperature_2m_max", [])[i]
            # TODO
            daily_weather.temp_night_min = daily.get("temperature_2m_min", [])[i]
            daily_weather.temp_night_max = daily.get("temperature_2m_min", [])[i]
            self._five_day_forecast.append(daily_weather)
        # current weather
        if not self._five_day_forecast:
            self._logger.warning("OpenMeteo: No daily forecast weather data received")
            return
        sunrise = self._five_day_forecast[0].sunrise
        sunset = self._five_day_forecast[0].sunset
        is_day = is_daytime(sunrise, sunset)
        self._current_weather = Weather(
            "",
            self._get_main_category(current_weather.get("weathercode", 0)),
            "",
            # current_weather.get("description"), # TODO detail
            datetime.now(),
            self._get_icon_name(current_weather.get("weathercode", ""), is_day),
            current_weather.get("windspeed", 0.0) * 3.6,  # km/h -> m/s
            current_weather.get("winddirection", 0.0),
            sunrise, sunset,
            1000.0,  # no data
            1000.0,  # no data, TODO get from hourly forecast
            0,  # TODO get from hourly forecast
            0.0,
            current_weather.get("temperature", 0.0),
            response.get("elevation", 0)
        )

        return self._current_weather

    def _complete_daily_weather(self): 
        # fill up current weather with hourly data
        if not self._current_weather:
            return
        weather_points = self.daytime_forecast_points[0] + self.nighttime_forecast_points[0]
        for point in weather_points:
            if point.date_time + timedelta(hours=1) > datetime.now():
                self._current_weather.humidity = point.humidity
                self._current_weather.clouds = point.clouds
                self._current_weather.pressure = point.pressure
                self._current_weather.pressure_sea_level = point.pressure_sea_level
                return

    def _fetch_hourly_weather(self):
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
        current_weather = self._current_weather
        if not current_weather:
            return ([], [])
        current_datetime = datetime.now()
        hourly = response.get("hourly", {})
        for i in range(len(hourly.get("time", []))):
            # utc to local time
            entry_date_time = datetime.fromisoformat(hourly.get("time", [])[i])
            time_delta = entry_date_time.date() - current_datetime.date()
            day_idx = time_delta.days
            if day_idx > 5 or day_idx < 0:
                continue
            is_day = is_daytime(current_weather.sunrise, current_weather.sunset, entry_date_time)
            weather_point = Weather(
                "",  # no name necessary
                hourly.get("weathercode", "")[i],
                "",
                entry_date_time,
                self._get_icon_name(hourly.get("weathercode", [])[i], is_day),
                hourly.get("windspeed_10m", [])[i],
                hourly.get("winddirection_10m", [])[i],
                current_weather.sunrise, current_weather.sunset,  # TODO use day
                hourly.get("surface_pressure", [])[i],
                hourly.get("pressure_msl", [])[i],
                hourly.get("relativehumidity_2m", [])[i],
                hourly.get("cloudcover", [])[i],
                hourly.get("temperature_2m", [])[i],
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

    def _get_icon_name(self, ident: int, is_day=False) -> str:
        """
        Helper function to get icon from condition.
        """
        if is_day:
            icon_name = om_day_code_to_ico.get(ident, "")
        else:
            icon_name = om_night_code_to_ico.get(ident, "")
        return icon_name

    def _get_main_category(self, ident: int) -> str:
        return om_condition_map.get(ident, "")

