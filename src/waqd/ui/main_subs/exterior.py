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
import datetime

from PyQt5 import QtCore

from waqd.assets import get_asset_file
from waqd.ui import common
from waqd.ui.main_subs import sub_ui
from waqd.ui.weather_detail_view import WeatherDetailView

Qt = QtCore.Qt


class Exterior(sub_ui.SubUi):
    """
    Exterior segment of the main ui.
    Displays the outside temperature, current-day forecast and temperature icon.
    """
    UPDATE_TIME = 10 * 1000  # 10 s in microseconds

    def __init__(self, main_ui, settings):
        super().__init__(main_ui, settings)
        self._online_info_date_time = None  # date when last online update occured

        # save default text to restore formatting
        self._default_temp_text = self._ui.exterior_temp_value.text()
        self._default_hum_text = self._ui.exterior_forecast_hum_value.text()

        day_icon = get_asset_file("weather_icons", "day-800")
        common.draw_svg(self._ui.exterior_forecast_icon, day_icon, scale=3)

        self._ui.exterior_forecast_icon.clicked.connect(self.show_detail)

        # set day temps to NA
        self._default_min_max_text = self._ui.exterior_forecast_temps_value.text()
        self._ui.exterior_forecast_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))
        # call once at begin
        self.init_with_cyclic_update()

    def show_detail(self):
        """ Daily detail view popup """
        [daytime_points, nighttime_points] = self._comps.weather_info.get_forecast_points()
        # after midnight nighttime_points[0] has points of both today and next day
        self.det = WeatherDetailView(daytime_points[0] + nighttime_points[0], self._settings, self._main_ui)
        self.det.show()

    def _cyclic_update(self):
        self._logger.debug("ExteriorGui: update")
        if not self._comps.weather_info:
            return
        forecast = self._comps.weather_info.get_5_day_forecast()
        current_weather = self._comps.weather_info.get_current_weather()
        temp_value = None
        hum_value = None

        if not current_weather or not forecast:  # handling for no connection - throw away value after an hour
            if self._online_info_date_time:  # look, if last value is older than 5 minutes
                current_date_time = datetime.datetime.now()
                time_delta = current_date_time - self._online_info_date_time
                if time_delta.seconds > 300:  # 5 minutes
                    temp_value = None
                else:
                    return  # forecast still valid, don't change displayed value
        else:
            self._online_info_date_time = current_weather.fetch_time
            temp_value = current_weather.temp  # for later use
            hum_value = current_weather.humidity
            online_weather_desc = current_weather.description
            self._logger.debug("ExteriorGui: Current weather condition is %s",
                               online_weather_desc)

            # set weather description specific background image
            online_weather_category = current_weather.main.lower()
            cloudiness = current_weather.clouds

            if cloudiness > 65 and online_weather_category == "clouds":
                online_weather_category = "heavy_clouds"

            if current_weather.is_daytime():
                bg_name = "bg_day_" + online_weather_category
            else:
                bg_name = "bg_night_" + online_weather_category

            self._ui.exterior_background.set_image(str(get_asset_file("weather_bgrs", bg_name)))

            # set todays forecast
            if not forecast[0]:
                return
            common.draw_svg(self._ui.exterior_forecast_icon, forecast[0].icon, scale=3)

            if not current_weather.is_daytime():
                temp_min = forecast[0].temp_night_min
                temp_max = forecast[0].temp_night_max
                if temp_min == -float("inf") or temp_max == float("inf"):
                    temp_min = forecast[0].temp_min
                    temp_max = forecast[0].temp_max
            else:
                temp_min = forecast[0].temp_min
                temp_max = forecast[0].temp_max
                if temp_min == -float("inf") or temp_max == float("inf"):
                    temp_min = forecast[0].temp_night_min
                    temp_max = forecast[0].temp_night_max

            self._ui.exterior_forecast_temps_value.setText(
                common.format_temp_text_minmax(self._default_min_max_text,
                                               temp_min, temp_max))

        # if sensor is available use it
        if self._comps.remote_exterior_sensor and not self._comps.remote_exterior_sensor.is_disabled:
            sensor_temp_value = self._comps.remote_exterior_sensor.get_temperature()
            if sensor_temp_value:
                temp_value = sensor_temp_value
            sensor_hum_value = self._comps.remote_exterior_sensor.get_humidity()
            if sensor_hum_value:
                hum_value = sensor_hum_value

        # format and set values to temperature display
        temp_val_text = common.format_float_temp_text(self._default_temp_text, temp_value)
        self._ui.exterior_temp_value.setText(temp_val_text)

        # format and set values to humidity display
        self._ui.exterior_forecast_hum_value.setText(common.format_int_meas_text(self._default_hum_text,
                                                                                 hum_value,
                                                                                 tag_id=1))

        # set temperature icon
        common.draw_svg(self._ui.exterior_temp_icon, common.get_temperature_icon(temp_value))
