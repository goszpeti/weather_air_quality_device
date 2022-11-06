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
from pint import Quantity
from typing import TYPE_CHECKING
from waqd.assets import get_asset_file
from waqd.base.network import Network
from waqd.app import unit_reg
from .. import common
from . import sub_ui
from ..weather_detail_view import WeatherDetailView

if TYPE_CHECKING:
    from waqd.ui.qt.main_ui import WeatherMainUi


Qt = QtCore.Qt


class Exterior(sub_ui.SubUi):
    """
    Exterior segment of the main ui.
    Displays the outside temperature, current-day forecast and temperature icon.
    """
    UPDATE_TIME = 10 * 1000  # 10 s in microseconds


    def __init__(self, main_ui: "WeatherMainUi", settings):
        super().__init__(main_ui, main_ui.ui, settings)
        self._online_info_date_time = None  # date when last online update occured
        self._comps = main_ui._comps

        # save default text to restore formatting
        self._default_temp_text = self._ui.exterior_temp_value.text()
        self._default_hum_text = self._ui.exterior_forecast_hum_value.text()
        # set default values
        temp_val_text = common.format_float_temp_text(self._default_temp_text, None)
        self._ui.exterior_temp_value.setText(temp_val_text)
        self._ui.exterior_forecast_hum_value.setText(common.format_int_meas_text(self._default_hum_text,
                                                                                 None,
                                                                                 tag_id=1))
        self.det = None
        na_icon = get_asset_file("weather_icons", "N/A")
        # common.draw_svg(self._ui.exterior_forecast_icon, na_icon, scale=3)
        common.draw_svg(self._ui.exterior_temp_icon, common.get_temperature_icon(
            Quantity(22, unit_reg.degC)))

        self._ui.exterior_forecast_icon.clicked.connect(self.show_detail)

        # set day temps to NA
        self._default_min_max_text = self._ui.exterior_forecast_temps_value.text()
        self._ui.exterior_forecast_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))
        # call once at begin
        Network().register_network_notification(main_ui.network_available_sig, self._cyclic_update)
        self.init_with_cyclic_update()

    def stop(self):
        super().stop()
        if self.det:
            del self.det

    def show_detail(self):
        """ Daily detail view popup """
        daytime_points = self._comps.weather_info.daytime_forecast_points
        nighttime_points = self._comps.weather_info.nighttime_forecast_points
        if not (nighttime_points or daytime_points):
            return
        # after midnight nighttime_points[0] has points of both today and next day
        self.det = WeatherDetailView(daytime_points[0] + nighttime_points[0], self._settings, self._main_ui)
        self.det.show()

    def _cyclic_update(self):
        self._logger.debug("ExteriorGui: update")
        if not self._comps.weather_info:
            return
        if not Network().internet_connected:
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
            temp_value = Quantity(current_weather.temp, unit_reg.degC)  # for later use
            hum_value = current_weather.humidity
            online_weather_desc = current_weather.description
            self._logger.debug("ExteriorGui: Current weather condition is %s",
                               online_weather_desc)
            weather_icon = current_weather.get_background_image()
            self._ui.exterior_background.set_image(str(weather_icon))

            # set todays forecast
            if not forecast[0]:
                return
            common.draw_svg(self._ui.exterior_forecast_icon, forecast[0].icon, scale=3)

            if not current_weather.is_daytime():
                temp_min = forecast[0].temp_night_min
                temp_max = forecast[0].temp_night_max
                if temp_min == -float("inf") or temp_max == float("inf"): # TODO
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
            temp_value = self._comps.remote_exterior_sensor.get_temperature()
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
