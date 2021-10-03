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
import time

from PyQt5 import QtGui

from waqd import config
from waqd.assets import get_asset_file
from waqd.settings import FORECAST_ENABLED, FORECAST_BG
from waqd.ui import common
from waqd.ui.main_subs import sub_ui

from waqd.ui.weather_detail_view import WeatherDetailView


class Forecast(sub_ui.SubUi):
    """  Forecast segment of the main ui. Displays the forecast for 3 days. """
    UPDATE_TIME = 600 * 1000  # 10 minutes in microseconds

    def __init__(self, qtui, settings):
        super().__init__(qtui, settings)
        self._default_min_max_text = self._ui.forecast_d1_day_temps_value.text()

        # set default day night icons - sunny clear
        day_icon = get_asset_file("weather_icons", "day-800")
        # night-clear
        night_icon = get_asset_file("weather_icons", "night-800")

        self._ui.forecast_background.setPixmap(QtGui.QPixmap(
            str(config.assets_path / "gui_bgrs" / settings.get(FORECAST_BG))))

        common.draw_svg(self._ui.forecast_d1_day_icon, day_icon)
        common.draw_svg(self._ui.forecast_d2_day_icon, day_icon)
        common.draw_svg(self._ui.forecast_d3_day_icon, day_icon)

        common.draw_svg(self._ui.forecast_d1_night_icon, night_icon)
        common.draw_svg(self._ui.forecast_d2_night_icon, night_icon)
        common.draw_svg(self._ui.forecast_d3_night_icon, night_icon)

        self._init_dummy_values()

        # connect daily detail view
        self._ui.forecast_d1_icon.clicked.connect(lambda: self.show_detail(1))
        self._ui.forecast_d2_icon.clicked.connect(lambda: self.show_detail(2))
        self._ui.forecast_d3_icon.clicked.connect(lambda: self.show_detail(3))

        # call once at begin
        self.init_with_cyclic_update()

    def _init_dummy_values(self):
        dummy_icon = str(get_asset_file("gui_base", "dummy-pic"))
        self._ui.forecast_d1_icon.setPixmap(QtGui.QPixmap(dummy_icon))
        self._ui.forecast_d2_icon.setPixmap(QtGui.QPixmap(dummy_icon))
        self._ui.forecast_d3_icon.setPixmap(QtGui.QPixmap(dummy_icon))

        # set day temps to NA
        self._ui.forecast_d1_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d2_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d3_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        # set night temps to NA
        self._ui.forecast_d1_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d2_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d3_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

    def show_detail(self, day):
        """ Detail view day 1 """
        [daytime_points, _] = self._comps.weather_info.get_forecast_points()
        self.det = WeatherDetailView(daytime_points[day], self._settings, self._main_ui)
        self.det.show()

    def _cyclic_update(self):
        self._logger.debug("ForecastGui: update")
        if not self._settings.get(FORECAST_ENABLED):
            self._logger.debug("ForecastGui: forecast disabled")
            return

        # set up titles
        current_date_time = datetime.datetime.now()

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=1), self._settings)
        self._ui.forecast_d1_title.setText(disp_date)

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=2), self._settings)
        self._ui.forecast_d2_title.setText(disp_date)

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=3), self._settings)
        self._ui.forecast_d3_title.setText(disp_date)

        # try three times to get weather info object
        i = 0
        while not self._comps.weather_info and i <= 3:
            i += 1
            time.sleep(1)
        if not self._comps.weather_info:
            return

        # get forecast info
        forecast = self._comps.weather_info.get_5_day_forecast()
        if not forecast or len(forecast) == 1:
            self._logger.debug("ForecastGui: No forecast information available")
            return

        # set icons
        common.draw_svg(self._ui.forecast_d1_icon, forecast[1].icon, scale=3.5)
        common.draw_svg(self._ui.forecast_d2_icon, forecast[2].icon, scale=3.5)
        common.draw_svg(self._ui.forecast_d3_icon, forecast[3].icon, scale=3.5)

        # set day temps
        self._ui.forecast_d1_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[1].temp_min,
                                           forecast[1].temp_max))

        self._ui.forecast_d2_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[2].temp_min,
                                           forecast[2].temp_max))

        self._ui.forecast_d3_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[3].temp_min,
                                           forecast[3].temp_max))

        # set night temps
        self._ui.forecast_d1_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[1].temp_night_min,
                                           forecast[1].temp_night_max))

        self._ui.forecast_d2_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[2].temp_night_min,
                                           forecast[2].temp_night_max))

        self._ui.forecast_d3_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[3].temp_night_min,
                                           forecast[3].temp_night_max))
