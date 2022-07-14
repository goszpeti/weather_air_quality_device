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
import threading
import time

from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

import waqd
from waqd.base.component_ctrl import ComponentController
from waqd.assets import get_asset_file
from waqd.settings import FONT_SCALING, FONT_NAME, Settings
from waqd.ui.main_subs import exterior, forecast, infopane, interior
from waqd.ui import common, options
from .qt.weather_ui import Ui_MainWindow

# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt


class WeatherMainUi(QtWidgets.QMainWindow):
    """ Base class of the main qt ui. Holds all the SubUi elements. """

    UPDATE_TIME = 1000  # microseconds
    OBJ_NAME = "WeatherMainUi"

    change_background_sig = QtCore.pyqtSignal(str)  # str arg is the message
    network_available_sig = QtCore.pyqtSignal()

    def __init__(self, comp_ctrl: ComponentController, settings: Settings):
        super().__init__()

        self.setObjectName(self.OBJ_NAME)
        self.ready = False

        self._comp_ctrl = comp_ctrl
        self._comps = comp_ctrl.components
        self._option_ui = None
        self._init_thread: Optional[threading.Thread] = None
        self._settings = settings

        self._ui = None
        self._exterior_ui: Optional[exterior.Exterior] = None
        self._interior_ui: Optional[interior.Interior] = None
        self._forecast_ui: Optional[forecast.Forecast] = None
        self._infopane_ui: Optional[infopane.InfoPane] = None

    @property
    def ui(self) -> Ui_MainWindow:
        """ Contains all gui objects defined in Qt .ui file. Subclasses need access to this. """
        return self._ui

    def eventFilter(self, source, event):  # pylint: disable=invalid-name
        """ Callback, to turn on the display on touch. """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # works currently with overriding the motion sensor
            if self._comps.motion_detection_sensor:
                cbck_thread = threading.Thread(
                    name="DisplayTurnOn",
                    target=self._comps.motion_detection_sensor._wake_up_from_sensor,
                    args=(None,), daemon=True)
                cbck_thread.start()
            self.hide_info_screen()
        return super().eventFilter(source, event)

    def init_gui(self):
        """ Retranslates, then loads all SubUi elements. """

        #ui_type = uic.loadUiType(config.base_path / "ui" / "qt" / "weather.ui")
        #self._ui = ui_type[0]()  # 0th element is always the UI class
        #self._ui.setupUi(self)
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        # scale before additional elments are initialized
        common.scale_gui_elements(self, self._settings.get_float(FONT_SCALING))

        # initialize all modules
        if not self._interior_ui:
            self._interior_ui = interior.Interior(self, self._settings)
        if not self._infopane_ui:
            self._infopane_ui = infopane.InfoPane(self, self._settings)
        if not self._forecast_ui:
            self._forecast_ui = forecast.Forecast(self, self._settings)
        if not self._exterior_ui:
            self._exterior_ui = exterior.Exterior(self, self._settings)

        common.apply_font(self, self._settings.get_string(FONT_NAME))

        common.apply_shadow_to_labels(self)

        # translate ui
        self._ui.retranslateUi(self)

        self.change_background_sig.connect(self._change_background)
        self._comps.event_handler.gui_background_update_sig = self.change_background_sig

        # connect buttons
        self._ui.info_button.clicked.connect(self.show_info_screen)

        self._ui.options_button.clicked.connect(self.show_options_window)

        self.hide_info_screen()
        self.installEventFilter(self)

        self.ready = True

    def unload_gui(self):
        """ Deletes all SubUi elements """

        # self._init_thread.join()

        if self._exterior_ui:
            self._exterior_ui.stop()
        if self._interior_ui:
            self._interior_ui.stop()
        if self._forecast_ui:
            self._forecast_ui.stop()
        if self._infopane_ui:
            self._infopane_ui.stop()

        del self._exterior_ui
        del self._interior_ui
        del self._forecast_ui
        del self._infopane_ui

        self._exterior_ui = None
        self._interior_ui = None
        self._forecast_ui = None
        self._infopane_ui = None

    def _change_background(self, file_id: str):
        """ Slot for change background signal """
        background = get_asset_file("gui_base", file_id)
        if background and background.is_file():
            while not self.ready:
                time.sleep(1)
            if not self._ui:
                return
            self._ui.interior_background.setPixmap(QtGui.QPixmap(str(background)))

    def show_options_window(self):
        """ Callback for Options button. Unloads this gui and starts the Options Gui."""
        self.ready = False
        # hold the option_ui as an instance variable for gc protection.
        # destroy a possible previous instance.
        while self._option_ui:
            del self._option_ui
            self._option_ui = None
            time.sleep(0)
        self.unload_gui()

        # unload all components, except those which forbid reload
        self._comp_ctrl.unload_all(reload_intended=True)
        self._option_ui = options.OptionMainUi(self, self._comp_ctrl, self._settings)

    def show_info_screen(self):
        """ Shows the user help overlay (opaque)."""
        if not self._ui:
            return
        self._ui.overlay_background.setPixmap(QtGui.QPixmap(str(get_asset_file("gui_base", "info_overlay"))))
        self._ui.overlay_background.raise_()
        self._ui.overlay_background.show()

        self._ui.ol_sensors_label.raise_()
        self._ui.ol_sensors_label.show()
        self._ui.ol_wh_today_label.raise_()
        self._ui.ol_wh_today_label.show()
        self._ui.ol_wh_forecast_label.raise_()
        self._ui.ol_wh_forecast_label.show()
        self._ui.ol_title_label.raise_()
        self._ui.ol_title_label.show()

    def hide_info_screen(self):
        """ Hides the user infro screen."""
        if not self._ui:
            return
        self._ui.overlay_background.hide()
        self._ui.ol_sensors_label.hide()
        self._ui.ol_wh_today_label.hide()
        self._ui.ol_title_label.hide()
        self._ui.ol_wh_forecast_label.hide()
