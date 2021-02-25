from PyQt5 import QtGui

from piweather.resources import get_rsc_file
from piweather.settings import DHT_22_DISABLED, DHT_22_PIN, BMP_280_ENABLED, CCS811_ENABLED, MH_Z19_ENABLED
from piweather.ui import common, sub_ui

BAR_INT_VALUE_HTML_TEXT = '<html><head/><body><p><span style="color:#ffffff;">0</span>' \
    '<span style=" color:#ffffff;"> {unit}</span></p></body></html>'


class Interior(sub_ui.SubUi):
    """ Interior segment of the main ui. Displays the interior sensor data. """
    UPDATE_TIME = 4 * 1000  # microseconds
    RSC_FOLDER = "gui_base"

    def __init__(self, main_ui, settings):
        super().__init__(main_ui, settings)
        self._tvoc_ui_element = self._ui.interior_3_value  # default on bar 3
        self._humidity_ui_element = self._ui.interior_1_value  # default on bar 1
        self._pressure_ui_element = None  # no default
        # save default text to restore formatting
        self._default_temp_text = self._ui.interior_temp_value.text()
        self._default_co2_text = self._ui.interior_co2_value.text()

        # set background
        self._ui.interior_background.setPixmap(QtGui.QPixmap(
            str(get_rsc_file(self.RSC_FOLDER, "bg_interior"))))

        # set up bars - logic, which bar is displayed:
        # CO2 is fix
        self._ui.interior_co2_bar.setPixmap(QtGui.QPixmap(
            str(get_rsc_file(self.RSC_FOLDER, "bar_co2"))))

        # set up humidty bar as default (it can change later)
        self._ui.interior_1_bar.setPixmap(QtGui.QPixmap(
            str(get_rsc_file(self.RSC_FOLDER, "bar_humidity"))))

        # if CCS811 is connected (TVOC enabled, )
        if self._settings.get(CCS811_ENABLED):
            self._ui.interior_3_bar.setPixmap(QtGui.QPixmap(
                str(get_rsc_file(self.RSC_FOLDER, "bar_tvoc"))))
            # bmp 280 connected, now look where pressure can be displayed.
            # TVOC will be replaced, or Humidity , if it is not available
            if self._settings.get(BMP_280_ENABLED):
                if self._settings.get(DHT_22_PIN) != DHT_22_DISABLED:
                    self._ui.interior_3_bar.setPixmap(QtGui.QPixmap(
                        str(get_rsc_file(self.RSC_FOLDER, "bar_pressure"))))
                    self._pressure_ui_element = self._ui.interior_3_value
                    self._tvoc_ui_element = None
                else:
                    self._ui.interior_1_bar.setPixmap(QtGui.QPixmap(
                        str(get_rsc_file(self.RSC_FOLDER, "bar_pressure"))))
                    self._pressure_ui_element = self._ui.interior_1_value
                    self._humidity_ui_element = None
        # in this case, there is no TVOC, so it can be replaced with pressure
        elif self._settings.get(MH_Z19_ENABLED):
            if self._settings.get(BMP_280_ENABLED):
                self._ui.interior_3_bar.setPixmap(QtGui.QPixmap(
                    str(get_rsc_file(self.RSC_FOLDER, "bar_pressure"))))
                self._pressure_ui_element = self._ui.interior_3_value
            else:
                self._tvoc_ui_element = None
                self._ui.interior_3_value.hide()
        else:
            self._tvoc_ui_element = None
            self._ui.interior_3_value.hide()

        # call once at begin
        self._cyclic_update()

    def _cyclic_update(self):
        self._logger.debug("InteriorGui: update")
        temp_value = self._comps.temp_sensor.get_temperature()
        pres_value = self._comps.pressure_sensor.get_pressure()
        hum_value = self._comps.humidity_sensor.get_humidity()
        tvoc_value = self._comps.tvoc_sensor.get_tvoc()
        co2_value = self._comps.co2_sensor.get_co2()

        # set temperature
        self._ui.interior_temp_value.setText(common.format_float_temp_text(
            self._default_temp_text, temp_value))

        # set temperature icon
        self._ui.interior_temp_icon.setPixmap(QtGui.QPixmap(
            str(common.get_temperature_icon(temp_value))))

        # set humidity
        if self._humidity_ui_element:
            label_text = BAR_INT_VALUE_HTML_TEXT.format(unit="%")
            self._humidity_ui_element.setText(
                common.format_int_meas_text(label_text, hum_value))

        # set pressure
        if self._pressure_ui_element:
            label_text = BAR_INT_VALUE_HTML_TEXT.format(unit="hPa")
            self._pressure_ui_element.setText(
                common.format_int_meas_text(label_text, pres_value))

        # set tvoc
        if self._tvoc_ui_element:
            label_color = "white"  # used as default font color
            # set to yellow if not stable
            if tvoc_value and not self._comps.tvoc_sensor.readings_stabilized:
                label_color = "yellow"
            label_text = BAR_INT_VALUE_HTML_TEXT.format(unit="ppb")
            self._tvoc_ui_element.setText(
                common.format_int_meas_text(label_text, tvoc_value, color=label_color))

        # set co2
        # set to yellow if not stable
        label_color = "white"  # used as default font color
        if co2_value:
            if not self._comps.co2_sensor.readings_stabilized:
                label_color = "yellow"
            elif co2_value >= 1200:
                label_color = "red"

        self._ui.interior_co2_value.setText(
            common.format_int_meas_text(self._default_co2_text, co2_value, color=label_color))
