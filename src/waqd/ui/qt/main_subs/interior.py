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
from typing import TYPE_CHECKING, Tuple

import waqd
from PyQt5 import QtGui
from waqd.app import unit_reg
from waqd.components.sensors import SENSOR_INTERIOR_TYPE
from waqd.settings import FONT_NAME, INTERIOR_BG
from waqd.ui import format_unit_disp_value
from waqd.ui.qt import common
from waqd.ui.qt.sensor_detail_view import SensorDetailView

from . import sub_ui

if TYPE_CHECKING:
    from waqd.settings import Settings
    from waqd.ui.qt.main_ui import WeatherMainUi

class Interior(sub_ui.SubUi):
    """ Interior segment of the main ui. Displays the interior sensor data. """
    UPDATE_TIME = 4 * 1000  # microseconds
    ASSETS_SUBFOLDER = "gui_base"
    BAR_TEXT_SIZE = 24
    HUM_BAR_OPTS = ("#125FCC", "#5A90DC", "RH")
    CO2_BAR_OPTS = ("#FF9F05", "#FFD623", "CO2")
    TVOC_BAR_OPTS = ("#2B9E36", "#B6FF00", "TVOC")
    PRES_BAR_OPTS = ("#7A3699", "#B48EC6", "BARO")

    def __init__(self, main_ui: "WeatherMainUi", settings: "Settings"):
        super().__init__(main_ui, main_ui.ui, settings)
        self._comps = main_ui._comps
        self._tvoc_ui_bar = None
        self._humidity_ui_bar = None
        self._pressure_ui_bar = None
        self._co2_bar = None
        self._default_temp_text = self._ui.interior_temp_value.text()
        self._ui_bars = [self._ui.interior_1_bar, self._ui.interior_2_bar, self._ui.interior_3_bar]
        self.det = None
        # set background
        self._ui.interior_background.setPixmap(QtGui.QPixmap(
            str(waqd.assets_path / "gui_bgrs" / settings.get_string(INTERIOR_BG))))

        self._ui.interior_1_bar.hide()
        self._ui.interior_2_bar.hide()
        self._ui.interior_3_bar.hide()

        font_name = self._settings.get_string(FONT_NAME)
        # check, which sensor are available:
        if not self._comps.humidity_sensor.is_disabled:
            self._humidity_ui_bar = self.set_available_bar(self.HUM_BAR_OPTS, font_name)

        if not self._comps.co2_sensor.is_disabled:
            self._co2_bar = self.set_available_bar(self.CO2_BAR_OPTS, font_name)

        if not self._comps.pressure_sensor.is_disabled:
            self._pressure_ui_bar = self.set_available_bar(self.PRES_BAR_OPTS, font_name)

        # TVOC is only displayed, if there is a bar free
        if not self._comps.tvoc_sensor.is_disabled:
            self._tvoc_ui_bar = self.set_available_bar(self.TVOC_BAR_OPTS, font_name)

        # connect sensor detail views
        self._ui.interior_temp_value.clicked.connect(
            lambda: self.show_detail("temp_degC", "°Celsius"))
        if self._co2_bar:
            self._co2_bar.clicked.connect(lambda: self.show_detail("CO2_ppm", "PPM"))
        if self._pressure_ui_bar:
            self._pressure_ui_bar.clicked.connect(lambda: self.show_detail("pressure_hPa", "hPa"))
        if self._tvoc_ui_bar:
            self._tvoc_ui_bar.clicked.connect(lambda: self.show_detail("TVOC", "PPB"))
        if self._humidity_ui_bar:
            self._humidity_ui_bar.clicked.connect(lambda: self.show_detail("humidity_%", "%"))

        # call once at begin
        self.init_with_cyclic_update()

    def stop(self):
        super().stop()
        if self.det:
            del self.det

    def set_available_bar(self, bar_opts: Tuple[str,str,str], font_name: str):
        for bar in self._ui_bars:
            if bar.isHidden():
                bar.setup_attributes(
                    *bar_opts, self.BAR_TEXT_SIZE, font_name)
                return bar
        return None

    def _cyclic_update(self):
        self._logger.debug("InteriorGui: update")
        temp_value = self._comps.temp_sensor.get_temperature()
        pres_value = self._comps.pressure_sensor.get_pressure()
        hum_value = self._comps.humidity_sensor.get_humidity()
        tvoc_value = self._comps.tvoc_sensor.get_tvoc()
        co2_value = self._comps.co2_sensor.get_co2()

        # set temperature - None check is done by functions
        self._ui.interior_temp_value.setText(common.format_float_temp_text(
            self._default_temp_text, temp_value))
        # set temperature icon
        common.draw_svg(self._ui.interior_temp_icon, common.get_temperature_icon(temp_value))

        # set humidity
        if self._humidity_ui_bar:
                self._humidity_ui_bar.set_value_label(format_unit_disp_value(hum_value, precision=0))

        # set pressure
        if self._pressure_ui_bar:
            self._pressure_ui_bar.set_value_label(format_unit_disp_value(pres_value, precision=0))

        # set tvoc
        if self._tvoc_ui_bar:
            label_color = "white"  # used as default font color
            # set to yellow if not stable
            if tvoc_value and not self._comps.tvoc_sensor.readings_stabilized:
                label_color = "yellow"
            self._tvoc_ui_bar.set_value_label(format_unit_disp_value(
                tvoc_value, precision=0), color=label_color)
    
        # set co2
        # set to yellow if not stable
        label_color = "white"  # used as default font color
        if self._co2_bar:
            if not self._comps.co2_sensor.readings_stabilized:
                label_color = "yellow"
            try:
                if co2_value.m_as(unit_reg.ppm) >= 1000:
                    label_color = "red"
            except:
                pass # no handling
            self._co2_bar.set_value_label(format_unit_disp_value(co2_value, precision=0), color=label_color)


    def show_detail(self, sensor_type: str, sensor_value_unit: str):
        """ Placholder for daily detail view popup """
        self.det = SensorDetailView(SENSOR_INTERIOR_TYPE, sensor_type, sensor_value_unit, self._main_ui)
