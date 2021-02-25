from PyQt5 import QtCore, QtGui, QtWidgets, uic
from piweather import __version__ as PIWHEATER_VERSION
from piweather import config
from piweather.base.component_ctrl import ComponentController
from piweather.base.system import RuntimeSystem
from piweather.resources import get_rsc_file
from piweather.settings import *
from piweather.ui import common
from piweather.ui.widgets.splashscreen import SplashScreen
from piweather.ui.widgets.fader_widget import FaderWidget

# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt


class OptionMainUi(QtWidgets.QDialog):
    """ Base class of the options qt ui. Holds the option SubUi element. """
    EXTRA_SCALING = 1.15  # make items bigger in this menu
    # matches strings to seconds in dropdown of timeouts
    TIME_CBOX_VALUES = {0: 5, 1: 30, 2: 120, 3: 600, 4: 1800}

    def __init__(self, main_ui: "WeatherMainUi", comp_ctrl: ComponentController, settings):
        super().__init__()

        self._main_ui = main_ui  # reference to main ui instance
        self._comp_ctrl = comp_ctrl
        self._comps = comp_ctrl.components
        self._settings = settings
        self._previous_scaling = self._settings.get(FONT_SCALING)
        self._runtime_system = RuntimeSystem()

        # create qt base objects
        self._qt_root_obj = self
        self._qt_root_obj.setWindowFlags(Qt.CustomizeWindowHint | Qt.FramelessWindowHint)

        ui_type = uic.loadUiType(config.base_path / "piweather" / "ui" /
                                 "qt" / "options.ui")
        self._ui = ui_type[0]()  # 0th element is always the UI class
        self._ui.setupUi(self)

        self._qt_root_obj.setGeometry(main_ui.qt_root_obj.geometry())

        # start fader - variable must be held otherwise gc will claim it
        fader_widget = FaderWidget(main_ui.qt_root_obj, self._qt_root_obj)  # pylint: disable=unused-variable

        # set version label
        self._ui.version_label.setText(PIWHEATER_VERSION)

        # display current options
        self.display_options()

        # connect buttons on main tab
        self._ui.ok_button.clicked.connect(self.apply_options)
        self._ui.cancel_button.clicked.connect(self.close_ui)
        self._ui.shutdown_button.clicked.connect(self.call_shutdown)
        self._ui.restart_button.clicked.connect(self.call_restart)

        self._ui.lang_combo_box.currentTextChanged.connect(self._update_language_cbox)

        # connect elements on gui tab
        self._ui.font_scaling_slider.valueChanged.connect(
            self.update_font_scaling_slider)
        self._ui.font_scaling_slider.sliderMoved.connect(
            self.update_font_scaling_slider)

        # connect elements on energy saver tab
        self._ui.night_mode_begin_slider.valueChanged.connect(
            self.update_night_mode_slider)
        self._ui.night_mode_begin_slider.sliderMoved.connect(
            self.update_night_mode_slider)

        self._ui.night_mode_end_slider.valueChanged.connect(
            self.update_night_mode_slider)
        self._ui.night_mode_end_slider.sliderMoved.connect(
            self.update_night_mode_slider)

        self._ui.brightness_slider.valueChanged.connect(
            self.update_brightness_slider)
        self._ui.brightness_slider.sliderMoved.connect(
            self.update_brightness_slider)

        self._ui.motion_sensor_enable_toggle.toggled.connect(
            self.update_motion_sensor_enabled)

        # set starting tab to first tab
        self._ui.options_tabs.setCurrentIndex(0)

        # set to normal brightness
        self._comps.display.set_brightness(self._settings.get(BRIGHTNESS))

        common.scale_gui_elements(
            self._qt_root_obj, self._settings.get(FONT_SCALING) * self.EXTRA_SCALING)

        # initialize splash screen for the closing of the UI and make a screenshot
        movie_file = get_rsc_file("gui_base", "option_spinner")
        movie = QtGui.QMovie(str(movie_file))
        self._splash_screen = SplashScreen(movie, background=False)
        self._qt_root_obj.show()

    def close_ui(self):
        """
        Transition back to Main Ui.
        Restart unloaded components and re-init main Gui.
        Shows splashscreen.
        """
        self._qt_root_obj.hide()
        # this splash screen works only in full screen under linux - god knows why...
        self._splash_screen.showFullScreen()
        while not self._comp_ctrl.all_unloaded:
            config.qt_app.processEvents()

        self._comp_ctrl.init_all()

        while not self._comp_ctrl.all_initialized:
            config.qt_app.processEvents()

        self._main_ui.init_gui()

        while not self._main_ui.ready:
            config.qt_app.processEvents()

        self._splash_screen.finish(self._main_ui.qt_root_obj)

        self._qt_root_obj.close()

    def apply_options(self):
        """
        Callback of Apply Options button.
        Write back every option and close ui.
        """
        settings = self._settings
        settings.set(LOCATION, self._ui.location_combo_box.currentText())
        settings.set(LANG, self._ui.lang_combo_box.currentText())
        settings.set(DAY_STANDBY_TIMEOUT, self.TIME_CBOX_VALUES.get(
            self._ui.day_standby_timeout_cbox.currentIndex()))
        settings.set(NIGHT_STANDBY_TIMEOUT, self.TIME_CBOX_VALUES.get(
            self._ui.night_standby_timeout_cbox.currentIndex()))

        settings.set(FONT_SCALING, self._ui.font_scaling_slider.sliderPosition() / 10)
        settings.set(EVENTS_ENABLED,  self._ui.events_enable_toggle.isChecked())

        settings.set(FORECAST_ENABLED, self._ui.forecast_enable_toggle.isChecked())
        settings.set(SOUND_ENABLED, self._ui.sound_enable_toggle.isChecked())
        settings.set(MOTION_SENSOR_ENABLED, self._ui.motion_sensor_enable_toggle.isChecked())

        settings.set(NIGHT_MODE_BEGIN, self._ui.night_mode_begin_slider.sliderPosition())
        settings.set(NIGHT_MODE_END, self._ui.night_mode_end_slider.sliderPosition())
        settings.set(BRIGHTNESS, self._ui.brightness_slider.sliderPosition())

        # write them to file
        settings.save_all_options()

        # update scaling on weather ui - needs to be done here, so previous scaling is available
        common.scale_gui_elements(self._main_ui.qt_root_obj,
                                  self._settings.get(FONT_SCALING), self._previous_scaling)
        # hide uis
        self.close_ui()

    def display_options(self):
        """ Set all elements to the display the current values and set up sliders """
        settings = self._settings
        self._ui.font_scaling_slider.setMinimum(10)
        self._ui.font_scaling_slider.setMaximum(20)
        self._ui.font_scaling_slider.setTickInterval(1)
        self._ui.font_scaling_slider.setSliderPosition(
            settings.get(FONT_SCALING) * 10)
        self._ui.font_scaling_value.setText(str(settings.get(FONT_SCALING)))

        self._ui.night_mode_begin_slider.setMaximum(24)
        self._ui.night_mode_begin_slider.setTickInterval(1)
        self._ui.night_mode_begin_value.setText(str(settings.get(NIGHT_MODE_BEGIN)))
        self._ui.night_mode_begin_slider.setSliderPosition(settings.get(NIGHT_MODE_BEGIN))

        self._ui.night_mode_end_slider.setMaximum(24)
        self._ui.night_mode_end_slider.setTickInterval(1)
        self._ui.night_mode_end_value.setText(str(settings.get(NIGHT_MODE_END)))
        self._ui.night_mode_end_slider.setSliderPosition(settings.get(NIGHT_MODE_END))

        self._ui.brightness_slider.setMaximum(100)
        self._ui.brightness_slider.setMinimum(30)
        self._ui.brightness_slider.setTickInterval(5)
        self._ui.brightness_value.setText(str(settings.get(BRIGHTNESS)))
        self._ui.brightness_slider.setSliderPosition(settings.get(BRIGHTNESS))

        self._ui.events_enable_toggle.setChecked(settings.get(EVENTS_ENABLED))

        # hw feature toggles
        self._ui.sound_enable_toggle.setChecked(settings.get(SOUND_ENABLED))
        self._ui.forecast_enable_toggle.setChecked(settings.get(FORECAST_ENABLED))
        self._ui.motion_sensor_enable_toggle.setChecked(settings.get(MOTION_SENSOR_ENABLED))
        self._ui.ccs811_enable_toggle.setChecked(settings.get(CCS811_ENABLED))
        self._ui.ccs811_enable_toggle.setDisabled(True)  # TODO
        self._ui.bmp280_enable_toggle.setChecked(settings.get(BMP_280_ENABLED))
        self._ui.bmp280_enable_toggle.setDisabled(True)
        self._ui.mh_z19_enable_toggle.setChecked(settings.get(MH_Z19_ENABLED))
        self._ui.mh_z19_enable_toggle.setDisabled(True)

        # set up DHT22 combo box
        dht_22_pin_list = ["Disabled", "4", "8", "22"]  # TODO
        self._ui.dht22_pin_cbox.addItems(dht_22_pin_list)
        # 0 is not in the list and means it is disabled, so it maps to 'Disabled'
        if str(settings.get(DHT_22_PIN)) not in dht_22_pin_list:
            selected_pin = 0
        else:
            selected_pin = dht_22_pin_list.index(str(settings.get(DHT_22_PIN)))

        self._ui.dht22_pin_cbox.setCurrentIndex(selected_pin)
        self._ui.dht22_pin_cbox.setDisabled(True)

        # set up display type combo box
        display_dict = {DISP_TYPE_RPI: "Original Raspberry Pi 7\" display",
                        DISP_TYPE_WAVESHARE: "Waveshare touch LCD display"}
        self._ui.display_type_cbox.setDisabled(True)
        self._ui.display_type_cbox.addItems(display_dict.values())
        self._ui.display_type_cbox.setCurrentIndex(
            list(display_dict.values()).index(display_dict.get(settings.get(DISPLAY_TYPE))))

        reverse_time_cbox_dict = dict([(v, k) for k, v in self.TIME_CBOX_VALUES.items()])

        self._ui.day_standby_timeout_cbox.setCurrentIndex(
            reverse_time_cbox_dict.get(settings.get(DAY_STANDBY_TIMEOUT)))
        self._ui.night_standby_timeout_cbox.setCurrentIndex(
            reverse_time_cbox_dict.get(settings.get(NIGHT_STANDBY_TIMEOUT)))

        # enable / disable standby based on motion sensor
        self._ui.day_standby_timeout_cbox.setEnabled(settings.get(MOTION_SENSOR_ENABLED))
        self._ui.night_standby_timeout_cbox.setEnabled(settings.get(MOTION_SENSOR_ENABLED))

        # populate location dropdown- only ow for now
        location_cb_element_count = self._ui.location_combo_box.count()
        for city in settings.get(OW_CITY_IDS):
            self._ui.location_combo_box.addItem("")
            self._ui.location_combo_box.setItemText(
                location_cb_element_count, city)
            location_cb_element_count += 1

        # set info labels
        self._ui.system_value.setText(self._runtime_system.platform)
        [ipv4, _] = self._runtime_system.get_ip()
        self._ui.ip_address_value.setText(ipv4)

        self._ui.location_combo_box.setCurrentText(
            settings.get(LOCATION))
        self._ui.lang_combo_box.setCurrentText(settings.get(LANG))

    def _update_language_cbox(self):
        """ Change language in the current ui on value change. """
        self._settings.set(LANG, self._ui.lang_combo_box.currentText())
        common.set_ui_language(config.qt_app, self._settings)
        self._ui.retranslateUi(self._qt_root_obj)
        self.display_options()  # redraw values

    def update_font_scaling_slider(self):
        """
        Callback to show font scaling value
        Because of rounding font info gets lost.
        Disable dynamic update for the time beeing.
        """
        self._ui.font_scaling_value.setText(str(self._ui.font_scaling_slider.sliderPosition() / 10))

    def update_night_mode_slider(self):
        """ Callback to update value shown on night mode time silder. """
        self._ui.night_mode_begin_value.setText(
            str(self._ui.night_mode_begin_slider.sliderPosition()))
        self._ui.night_mode_end_value.setText(
            str(self._ui.night_mode_end_slider.sliderPosition()))

    def update_brightness_slider(self):
        """ Callback to update value shown on brightness silder. """
        self._ui.brightness_value.setText(
            str(self._ui.brightness_slider.sliderPosition()))
        self._comps.display.set_brightness(
            self._ui.brightness_slider.sliderPosition())

    def call_shutdown(self):
        """ Callback to shut down the target system. """
        self._runtime_system.shutdown()
        self.close_ui()

    def call_restart(self):
        """ Callback to restart the target system. """
        self._runtime_system.restart()
        self.close_ui()

    def update_motion_sensor_enabled(self):
        """ Callback to disable the timeout checkboxes, if motion sensor is checked. """
        value = bool(
            self._ui.motion_sensor_enable_toggle.isChecked())
        self._ui.day_standby_timeout_cbox.setEnabled(value)
        self._ui.night_standby_timeout_cbox.setEnabled(value)

    def _cyclic_update(self):
        pass
