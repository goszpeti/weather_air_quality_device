#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of ProjectName
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
import time
from subprocess import check_output
from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtGui

from waqd import __version__ as WAQD_VERSION
import waqd
from waqd.base.component_ctrl import ComponentController
from waqd.base.network import Network
from waqd.base.system import RuntimeSystem
from waqd.base.translation import Translation
from waqd.components.sensors import MH_Z19
from waqd.settings import (BME_280_ENABLED, BMP_280_ENABLED, BRIGHTNESS, CCS811_ENABLED,
                           DAY_STANDBY_TIMEOUT, DHT_22_DISABLED, DHT_22_PIN, DISP_TYPE_RPI,
                           DISP_TYPE_WAVESHARE_5_LCD, DISPLAY_TYPE,
                           EVENTS_ENABLED, FONT_NAME, FONT_SCALING, AUTO_UPDATER_ENABLED,
                           LANG, LOCATION, MOTION_SENSOR_ENABLED, MH_Z19_ENABLED,
                           NIGHT_MODE_BEGIN, NIGHT_MODE_END, INTERIOR_BG, FORECAST_BG,
                           NIGHT_STANDBY_TIMEOUT, OW_CITY_IDS, LOG_SENSOR_DATA,
                           SOUND_ENABLED, UPDATER_USER_BETA_CHANNEL, MH_Z19_VALUE_OFFSET, Settings)
from . import common
from waqd.ui.qt.theming import activate_theme
from waqd.ui.qt.main_subs import sub_ui
from waqd.ui.qt.widgets.fader_widget import FaderWidget
from waqd.ui.qt.widgets.splashscreen import SplashScreen
from PyQt5.QtWidgets import QScroller, QApplication, QPushButton, QMessageBox, QDialog, QDialogButtonBox, QWidget
from .qt.options_ui import Ui_Dialog

# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt

if TYPE_CHECKING:
    from waqd.ui.qt.main_ui import WeatherMainUi


class OptionMainUi(QDialog):
    """ Base class of the options qt ui. Holds the option SubUi element. """
    EXTRA_SCALING = 1.15  # make items bigger in this menu
    # matches strings to seconds in dropdown of timeouts
    TIME_CBOX_VALUES = [5, 30, 120, 600, 1800]  # seconds
    FONT_SCALING_VALUES = [0.7, 0.85, 1]
    DHT_PIN_VALUES = ["Disabled", "4", "8", "22"]

    def __init__(self, main_ui: "WeatherMainUi", comp_ctrl: ComponentController, settings: Settings):
        super().__init__()
        self._main_ui = main_ui  # reference to main ui instance
        self._comp_ctrl = comp_ctrl
        self._comps = comp_ctrl.components
        self._settings = settings
        self._previous_scaling = self._settings.get(FONT_SCALING)
        self._runtime_system = RuntimeSystem()

        # create qt base objects
        self.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint | Qt.FramelessWindowHint))

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)
        activate_theme(self._settings.get_float(FONT_SCALING), self._settings.get_string(FONT_NAME))
        self.setGeometry(main_ui.geometry())

        # start fader - variable must be held otherwise gc will claim it
        fader_widget = FaderWidget(main_ui, self)  # pylint: disable=unused-variable

        # set version label
        self._ui.version_label.setText(WAQD_VERSION)

        self._ui.general_button.clicked.connect(self._switch_pages)
        self._ui.display_button.clicked.connect(self._switch_pages)
        self._ui.theme_button.clicked.connect(self._switch_pages)
        self._ui.events_button.clicked.connect(self._switch_pages)
        self._ui.hw_button.clicked.connect(self._switch_pages)
        self._ui.about_button.clicked.connect(self._switch_pages)

        self._ui.general_button.click()
        # display current options
        self.display_options()

        # connect buttons on main tab
        self._ui.ok_button.clicked.connect(self.apply_options)
        self._ui.cancel_button.clicked.connect(self.close_ui)
        self._ui.shutdown_button.clicked.connect(self.call_shutdown)
        self._ui.restart_button.clicked.connect(self.call_restart)
        self._ui.connect_wlan_button.clicked.connect(self._connect_wlan)
        self._ui.mh_z19_calibrate_button.clicked.connect(self._calibrate_mh_z19)
        self._ui.motion_sensor_test_button.clicked.connect(self._test_motion_sensor)
        self._ui.reset_pw_button.clicked.connect(self._reset_pw)

        self._ui.lang_cbox.currentTextChanged.connect(self._update_language_cbox)
        self._ui.forecast_background_cbox.currentTextChanged.connect(self._update_preview_forecast)
        self._ui.interior_background_cbox.currentTextChanged.connect(self._update_preview_interior)
        self._ui.font_cbox.currentFontChanged.connect(self._update_font)

        # connect elements on energy saver tab
        self._ui.night_mode_begin_slider.valueChanged.connect(
            self._update_night_mode_slider)
        self._ui.night_mode_begin_slider.sliderMoved.connect(
            self._update_night_mode_slider)

        self._ui.night_mode_end_slider.valueChanged.connect(
            self._update_night_mode_slider)
        self._ui.night_mode_end_slider.sliderMoved.connect(
            self._update_night_mode_slider)

        self._ui.brightness_slider.valueChanged.connect(
            self._update_brightness_slider)
        self._ui.brightness_slider.sliderMoved.connect(
            self._update_brightness_slider)

        self._ui.motion_sensor_enable_toggle.toggled.connect(
            self._update_motion_sensor_enabled)

        # set starting tab to first tab
        # self._ui.options_tabs.setCurrentIndex(0)
        QScroller.grabGesture(self._ui.hw_scroll_area, QScroller.LeftMouseButtonGesture)
        # set to normal brightness
        while not comp_ctrl.all_unloaded:
            time.sleep(0.1)
        self._comps.display.set_brightness(self._settings.get_int(BRIGHTNESS))

        # initialize splash screen for the closing of the UI and make a screenshot
        self._splash_screen = SplashScreen(background=False)
        # minimal wait to show the button feedback
        time.sleep(0.3)
        self.show()

    def _switch_pages(self):
        sender_button = self.sender()
        assert isinstance(sender_button, QPushButton), "Switch page can only be triggered from a button!"
        obj_name = sender_button.objectName()
        if obj_name == "display_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.display_page)
        elif obj_name == "general_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.general_page)
        elif obj_name == "theme_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.theme_page)
        elif obj_name == "events_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.events_page)
        elif obj_name == "hw_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.hw_page)
        elif obj_name == "about_button":
            self._ui.page_stacked_widget.setCurrentWidget(self._ui.about_page)

    def _calibrate_mh_z19(self):
        from .widgets.calibration_ui import Ui_Dialog
        self._calib_dialog = QDialog(self)
        self._calib_dialog_ui = Ui_Dialog()
        self._calib_dialog_ui.setupUi(self._calib_dialog)
        self._calib_dialog.setModal(True)
        # check if it is the correct one
        if not isinstance(self._comps.co2_sensor, MH_Z19):
            msg = QMessageBox(parent=self)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
            msg.setIcon(QMessageBox.Critical)
            msg.setText("MH-Z19 is currently not available.")
            msg.setModal(True)
            msg.adjustSize()
            msg.show()
            msg.move(int((self.geometry().width() - msg.width()) / 2),
                    int((self.geometry().height() - msg.height()) / 2))
            msg.exec_()
            return
        offset = self._settings.get_int(MH_Z19_VALUE_OFFSET)
        self._calib_dialog.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
        self._calib_dialog.adjustSize()
        self._calib_dialog.move(int((self.geometry().width() - self._calib_dialog.width()) / 2),
                                int((self.geometry().height() - self._calib_dialog.height()) / 2))
        self._calib_dialog_ui.calib_spin_box.setValue(offset)
        self._calib_dialog_ui.calib_spin_box.valueChanged.connect(self._update_calib_value)
        self._calib_dialog_ui.zero_button.clicked.connect(self._comps.co2_sensor.zero_calibraton)
        self._calib_dialog_ui.button_box.button(
            QDialogButtonBox.Save).clicked.connect(self._save_mh_z19_calib)
        self._update_calib_value()
        self._calib_dialog.exec_()

    def _update_calib_value(self):
        offset = self._calib_dialog_ui.calib_spin_box.value()
        meas_value = self._comps.co2_sensor.get_co2()
        self._calib_dialog_ui.measure_value_label.setText(str(meas_value))
        if meas_value:
            self._calib_dialog_ui.display_value_label.setText(str(meas_value + offset))

    def _save_mh_z19_calib(self):
        if self._calib_dialog_ui:
            offset = self._calib_dialog_ui.calib_spin_box.value()
            self._settings.set(MH_Z19_VALUE_OFFSET, offset)
            self._comps.stop_component_instance(self._comps.co2_sensor)

    def _test_motion_sensor(self):
        class MotionSensorTestDialog(sub_ui.SubUi):
            def __init__(self, parent: QWidget, comps, settings) -> None:
                from .widgets.value_test_ui import Ui_Dialog
                self._comps = comps
                self._dialog = QDialog(parent)
                self._dialog.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
                self._ui = Ui_Dialog()
                self._ui.setupUi(self._dialog)
                sub_ui.SubUi.__init__(self, self._dialog, self._ui, settings)
                #self._dialog.adjustSize()
                self._dialog.move(int((parent.geometry().width() - self._dialog.width()) / 2),
                                  int((parent.geometry().height() - self._dialog.height()) / 2)
                                  )

            def _cyclic_update(self):
                if self._comps.motion_detection_sensor.motion_detected:
                    disp_str = Translation().get_localized_string(
                        "ui_dict", "motion_reg", self._settings.get_string(LANG))
                    self._ui.text_browser.append(disp_str)
                else:
                    disp_str = Translation().get_localized_string(
                        "ui_dict", "no_motion_reg", self._settings.get_string(LANG))
                    self._ui.text_browser.append(disp_str)

            def exec_(self):
                self._dialog.exec_()

        dialog = MotionSensorTestDialog(self, self._comps, self._settings)
        dialog.exec_()

    def display_options(self):
        """ Set all elements to the display the current values and set up sliders """
        settings = self._settings

        # read events
        events_json_path = waqd.user_config_dir / "events.json"
        if events_json_path.exists():
            with open(events_json_path, "r") as fp:
                events_text = fp.read()
                self._ui.event_config_text_browser.setText(events_text)
        self._ui.night_mode_begin_slider.setMaximum(24)
        self._ui.night_mode_begin_slider.setTickInterval(1)
        self._ui.night_mode_begin_value.setText(str(settings.get(NIGHT_MODE_BEGIN)))
        self._ui.night_mode_begin_slider.setSliderPosition(settings.get_int(NIGHT_MODE_BEGIN))

        self._ui.night_mode_end_slider.setMaximum(24)
        self._ui.night_mode_end_slider.setTickInterval(1)
        self._ui.night_mode_end_value.setText(str(settings.get(NIGHT_MODE_END)))
        self._ui.night_mode_end_slider.setSliderPosition(settings.get_int(NIGHT_MODE_END))

        self._ui.brightness_slider.setMaximum(100)
        self._ui.brightness_slider.setMinimum(30)
        self._ui.brightness_slider.setTickInterval(5)
        self._ui.brightness_value.setText(str(settings.get(BRIGHTNESS)))
        self._ui.brightness_slider.setSliderPosition(settings.get_int(BRIGHTNESS))

        self._ui.events_enable_toggle.setChecked(settings.get(EVENTS_ENABLED))
        self._ui.auto_updater_enable_toggle.setChecked(settings.get(AUTO_UPDATER_ENABLED))
        self._ui.sensor_logging_enable_toggle.setChecked(settings.get(LOG_SENSOR_DATA))
        self._ui.updater_beta_channel_toggle.setChecked(settings.get(UPDATER_USER_BETA_CHANNEL))

        # themes
        # set background images
        bgr_path = waqd.assets_path / "gui_bgrs"
        for bgr_file in bgr_path.iterdir():
            self._ui.interior_background_cbox.addItem(bgr_file.name)
            self._ui.forecast_background_cbox.addItem(bgr_file.name)

        self._ui.interior_background_cbox.setCurrentText(settings.get_string(INTERIOR_BG))
        self._ui.forecast_background_cbox.setCurrentText(settings.get_string(FORECAST_BG))
        self._ui.font_cbox.setCurrentText(settings.get_string(FONT_NAME))
        # try to get index - font-scaling can be set to anything
        try:
            scaling_index = self.FONT_SCALING_VALUES.index(self._previous_scaling)
        except Exception:  # normal
            scaling_index = 1
        self._ui.font_scaling_cbox.setCurrentIndex(scaling_index)

        # hw feature toggles
        self._ui.sound_enable_toggle.setChecked(settings.get_bool(SOUND_ENABLED))
        self._ui.motion_sensor_enable_toggle.setChecked(settings.get_bool(MOTION_SENSOR_ENABLED))
        self._ui.ccs811_enable_toggle.setChecked(settings.get_bool(CCS811_ENABLED))
        self._ui.bmp280_enable_toggle.setChecked(settings.get_bool(BMP_280_ENABLED))
        self._ui.bme280_enable_toggle.setChecked(settings.get_bool(BME_280_ENABLED))
        self._ui.mh_z19_enable_toggle.setChecked(settings.get_bool(MH_Z19_ENABLED))

        # set up DHT22 combo box
        self._ui.dht22_pin_cbox.addItems(self.DHT_PIN_VALUES)
        # 0 is not in the list and means it is disabled, so it maps to 'Disabled'
        if str(settings.get(DHT_22_PIN)) not in self.DHT_PIN_VALUES:
            selected_pin = 0
        else:
            selected_pin = self.DHT_PIN_VALUES.index(str(settings.get(DHT_22_PIN)))

        self._ui.dht22_pin_cbox.setCurrentIndex(selected_pin)

        # set up display type combo box
        display_dict = {DISP_TYPE_RPI: "Org. RPi 7\" display",
                        DISP_TYPE_WAVESHARE_5_LCD: "Waveshare touch LCD"}
        self._ui.display_type_cbox.setDisabled(True)
        self._ui.display_type_cbox.addItems(display_dict.values())

        try:
            self._ui.display_type_cbox.setCurrentIndex(
                list(display_dict.values()).index(display_dict[settings.get_string(DISPLAY_TYPE)]))
            self._ui.day_standby_timeout_cbox.setCurrentIndex(
                self.TIME_CBOX_VALUES.index(settings.get_int(DAY_STANDBY_TIMEOUT)))
            self._ui.night_standby_timeout_cbox.setCurrentIndex(
                self.TIME_CBOX_VALUES.index(settings.get_int(NIGHT_STANDBY_TIMEOUT)))
        except Exception:  # leave default
            pass

        # enable / disable standby based on motion sensor
        self._ui.day_standby_timeout_cbox.setEnabled(settings.get_bool(MOTION_SENSOR_ENABLED))
        self._ui.night_standby_timeout_cbox.setEnabled(settings.get_bool(MOTION_SENSOR_ENABLED))

        # populate location dropdown- only ow for now
        self._ui.location_combo_box.clear()
        for city in settings.get_dict(OW_CITY_IDS).keys():
            self._ui.location_combo_box.addItem(city)
        self._ui.location_combo_box.setCurrentText(settings.get_string(LOCATION))
        if waqd.DEBUG_LEVEL < 1:
            self._ui.location_combo_box.setDisabled(True)  # one location for now
        # set info labels
        self._ui.system_value.setText(self._runtime_system.platform.replace("_", " "))
        [ipv4, _] = Network().get_ip()
        self._ui.ip_address_value.setText(ipv4)
        self._ui.lang_cbox.setCurrentText(settings.get_string(LANG))

        # set to normal brightness - again, in case it was modified
        self._comps.display.set_brightness(self._settings.get_int(BRIGHTNESS))

    def close_ui(self):
        """
        Transition back to Main Ui.
        Restart unloaded components and re-init main Gui.
        Shows splashscreen.
        """
        # minimal wait to show the button feedback
        time.sleep(0.3)
        self.hide()
        # this splash screen works only in full screen under RPI - god knows why...
        if self._runtime_system.is_target_system:
            self._splash_screen.showFullScreen()
            self._splash_screen.setFocus()
        else:
            self._splash_screen.show()
        loading_minimum_time = 3  # seconds
        start = time.time()
        while not self._comp_ctrl.all_unloaded or (time.time() < start + loading_minimum_time):
            QApplication.processEvents()

        self._comp_ctrl.init_all()

        while not self._comp_ctrl.all_ready:
            QApplication.processEvents()

        self._main_ui.init_gui()
        start = time.time()
        while not self._main_ui.ready or (time.time() < start + loading_minimum_time):
            QApplication.processEvents()

        self._splash_screen.finish(self._main_ui)

        self.close()

    def apply_options(self):
        """
        Callback of Apply Options button.
        Write back every option and close ui.
        """
        settings = self._settings
        settings.set(LOCATION, self._ui.location_combo_box.currentText())
        settings.set(LANG, self._ui.lang_cbox.currentText())
        settings.set(DAY_STANDBY_TIMEOUT, self.TIME_CBOX_VALUES[
            self._ui.day_standby_timeout_cbox.currentIndex()])
        settings.set(NIGHT_STANDBY_TIMEOUT, self.TIME_CBOX_VALUES[
            self._ui.night_standby_timeout_cbox.currentIndex()])

        settings.set(EVENTS_ENABLED,  self._ui.events_enable_toggle.isChecked())
        settings.set(LOG_SENSOR_DATA,  self._ui.sensor_logging_enable_toggle.isChecked())

        settings.set(UPDATER_USER_BETA_CHANNEL,  self._ui.updater_beta_channel_toggle.isChecked())
        settings.set(AUTO_UPDATER_ENABLED, self._ui.auto_updater_enable_toggle.isChecked())
        settings.set(SOUND_ENABLED, self._ui.sound_enable_toggle.isChecked())

        settings.set(NIGHT_MODE_BEGIN, self._ui.night_mode_begin_slider.sliderPosition())
        settings.set(NIGHT_MODE_END, self._ui.night_mode_end_slider.sliderPosition())
        settings.set(BRIGHTNESS, self._ui.brightness_slider.sliderPosition())

        settings.set(INTERIOR_BG, self._ui.interior_background_cbox.currentText())
        settings.set(FORECAST_BG, self._ui.forecast_background_cbox.currentText())
        settings.set(FONT_NAME, self._ui.font_cbox.currentText())

        if self._ui.dht22_pin_cbox.currentText() == self.DHT_PIN_VALUES[0]:  # "Disabled"
            settings.set(DHT_22_PIN, DHT_22_DISABLED)
        else:
            settings.set(DHT_22_PIN, int(self._ui.dht22_pin_cbox.currentText()))
        settings.set(MOTION_SENSOR_ENABLED, self._ui.motion_sensor_enable_toggle.isChecked())
        settings.set(BME_280_ENABLED, self._ui.bme280_enable_toggle.isChecked())
        settings.set(BMP_280_ENABLED, self._ui.bmp280_enable_toggle.isChecked())
        settings.set(MH_Z19_ENABLED, self._ui.mh_z19_enable_toggle.isChecked())
        settings.set(CCS811_ENABLED, self._ui.ccs811_enable_toggle.isChecked())

        font_scaling = self.FONT_SCALING_VALUES[self._ui.font_scaling_cbox.currentIndex()]
        self._settings.set(FONT_SCALING, font_scaling)

        # write them to file
        settings.save()

        self.close_ui()

    def _update_language_cbox(self):
        """ Change language in the current ui on value change. """
        self._settings.set(LANG, self._ui.lang_cbox.currentText())
        common.set_ui_language(QApplication.instance(), self._settings)
        self._ui.retranslateUi(self)
        self.display_options()  # redraw values

    def _update_font(self):
        font = self._ui.font_cbox.currentFont()
        self.setFont(font)
        QApplication.instance().setFont(font)

    def _update_preview_interior(self):
        bgr_path = waqd.assets_path / "gui_bgrs" / self._ui.interior_background_cbox.currentText()
        self._ui.preview_label.setPixmap(QtGui.QPixmap(str(bgr_path)))

    def _update_preview_forecast(self):
        bgr_path = waqd.assets_path / "gui_bgrs" / self._ui.forecast_background_cbox.currentText()
        self._ui.preview_label.setPixmap(QtGui.QPixmap(str(bgr_path)))

    def _update_night_mode_slider(self):
        """ Callback to update value shown on night mode time silder. """
        self._ui.night_mode_begin_value.setText(
            str(self._ui.night_mode_begin_slider.sliderPosition()))
        self._ui.night_mode_end_value.setText(
            str(self._ui.night_mode_end_slider.sliderPosition()))

    def _update_brightness_slider(self):
        """ Callback to update value shown on brightness silder. """
        self._ui.brightness_value.setText(
            str(self._ui.brightness_slider.sliderPosition()))
        self._comps.display.set_brightness(
            self._ui.brightness_slider.sliderPosition())

    def _update_motion_sensor_enabled(self):
        """ Callback to disable the timeout checkboxes, if motion sensor is checked. """
        value = bool(
            self._ui.motion_sensor_enable_toggle.isChecked())
        self._ui.day_standby_timeout_cbox.setEnabled(value)
        self._ui.night_standby_timeout_cbox.setEnabled(value)

    def call_shutdown(self):
        """ Callback to shut down the target system. """
        self._runtime_system.shutdown()
        self.close_ui()

    def call_restart(self):
        """ Callback to restart the target system. """
        self._runtime_system.restart()
        self.close_ui()

    def _reset_pw(self):
        msg = QMessageBox(parent=self)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Reset Password")
        from waqd.base.authentification import DEFAULT_USERNAME, bcrypt

        new_pw = bcrypt.gensalt(4).decode("utf-8")[18:]
        # self._settings.set(USER_DEFAULT_PW, new_pw) TODO unsafe
        self._comps.server.user_auth.set_password(DEFAULT_USERNAME, new_pw)
        disp_str = Translation().get_localized_string(
            "ui_dict", "new_pw_text", self._settings.get_string(LANG))
        msg.setText(disp_str.format(user_name=DEFAULT_USERNAME, pw=new_pw))
        msg.adjustSize()
        msg.show()
        msg.move(int((self.geometry().width() - msg.width()) / 2),
                 int((self.geometry().height() - msg.height()) / 2))
        msg.exec_()
        msg.width()

    def _connect_wlan(self):
        ssid_name = "Connect_WAQD"
        msg = QMessageBox(parent=self)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
        # shutdown server, so port 80 is free for captive portal
        self._comps.stop_component_instance(self._comps.server)  # should start autom. after options closes
        msg.setIcon(QMessageBox.Information)
        disp_str = Translation().get_localized_string(
            "ui_dict", "wlan_portal_help", self._settings.get_string(LANG))
        msg.setText(disp_str.format(ssid_name=ssid_name))
        # needed because of CustomizeWindowHint
        msg.adjustSize()
        msg.show()
        msg.move(int((self.geometry().width() - msg.width()) / 2),
                 int((self.geometry().height() - msg.height()) / 2))
        msg.accepted.connect(self._run_wlan_portal)
        msg.exec_()

    def _run_wlan_portal(self):
        ssid_name = "Connect_WAQD"
        try:
            check_output(["sudo", "wifi-connect", "-s", f'"{ssid_name}"'])
        except Exception as e:
            msg = QMessageBox(parent=self)
            msg.setStandardButtons(QMessageBox.Ok, )
            msg.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
            msg.setIcon(QMessageBox.Warning)
            disp_str = Translation().get_localized_string("ui_dict",
                                                          "wlan_error_text", self._settings.get_string(LANG))
            msg.setText(f"{disp_str} {str(e)}")
            # needed because of CustomizeWindowHint
            msg.adjustSize()
            msg.show()
            msg.move(int((self.geometry().width() - msg.width()) / 2),
                     int((self.geometry().height() - msg.height()) / 2))
            msg.exec_()

    def _cyclic_update(self):
        pass
