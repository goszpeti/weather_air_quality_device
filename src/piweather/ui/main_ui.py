import threading
import time

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from piweather import config
from piweather.base.component_ctrl import ComponentController
from piweather.base.logger import Logger
from piweather.base.system import RuntimeSystem
from piweather.resources import get_rsc_file
from piweather.settings import FONT_SCALING, Settings
from piweather.ui.main_subs import exterior, forecast, infopane, interior
from piweather.ui import common, options

# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt


class WeatherMainUi(QtWidgets.QMainWindow):
    """ Base class of the main qt ui. Holds all the SubUi elements. """

    UPDATE_TIME = 1000  # microseconds
    OBJ_NAME = "WeatherMainUi"

    change_background_sig = QtCore.pyqtSignal(str)  # str arg is the message

    def __init__(self, comp_ctrl: ComponentController, settings: Settings):
        super().__init__()

        self.setObjectName(self.OBJ_NAME)
        self.ready = False

        self._comp_ctrl = comp_ctrl
        self._comps = comp_ctrl.components
        self._logger = Logger()
        self._option_ui = None
        self._init_thread: threading.Thread = None
        self._settings = settings
        self._runtime_system = RuntimeSystem()

        self._qt_root_obj = self  # TODO
        self._ui = None
        self._exterior_ui: exterior.Exterior = None
        self._interior_ui: interior.Interior = None
        self._forecast_ui: forecast.Forecast = None
        self._infopane_ui: infopane.InfoPane = None

    @property
    def ui(self):
        """ Contains all gui objects defined in Qt .ui file. Subclasses need access to this. """
        return self._ui

    @property
    def qt_root_obj(self):
        """ The base class of this ui. Is needed to pass as parent ot call show and hide. """
        return self._qt_root_obj

    def eventFilter(self, source, event):  # pylint: disable=invalid-name
        """ Callback, to turn on the display on touch. """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # works currently with overriding the motion sensor
            if self._comps.motion_detection_sensor:
                cbck_thread = threading.Thread(
                    target=self._comps.motion_detection_sensor._wake_up_from_sensor,
                    args=(None,), daemon=True)
                cbck_thread.start()
        return super().eventFilter(source, event)

    def init_gui(self):
        """ Retranslates, then loads all SubUi elements. """
        ui_type = uic.loadUiType(config.base_path / "piweather" / "ui" / "qt" / "weather.ui")
        self._ui = ui_type[0]()  # 0th element is always the UI class
        self._ui.setupUi(self)

        # initial scaling
        common.scale_gui_elements(self._qt_root_obj, self._settings.get(FONT_SCALING))

        # translate ui
        self._ui.retranslateUi(self._qt_root_obj)

        self.change_background_sig.connect(self._change_background)
        self._comps.event_handler.gui_background_update_sig = self.change_background_sig

        # connect buttons
        if self._runtime_system.is_target_system and config.DEBUG_LEVEL == 0:
            self._ui.exit_button.clicked.connect(self._runtime_system.shutdown)
        else:
            self._ui.exit_button.clicked.connect(self._qt_root_obj.close)

        self._ui.options_button.clicked.connect(self.show_options_window)
        self._qt_root_obj.installEventFilter(self)

        # initialize all modules
        if not self._interior_ui:
            self._interior_ui = interior.Interior(self, self._settings)
        if not self._infopane_ui:
            self._infopane_ui = infopane.InfoPane(self, self._settings)
        if not self._forecast_ui:
            self._forecast_ui = forecast.Forecast(self, self._settings)
        if not self._exterior_ui:
            self._exterior_ui = exterior.Exterior(self, self._settings)
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

        self._exterior_ui: exterior.Exterior = None
        self._interior_ui: interior.Interior = None
        self._forecast_ui: forecast.Forecast = None
        self._infopane_ui: infopane.InfoPane = None

    def _change_background(self, file_id: str):
        """ Slot for change background signal """
        background = get_rsc_file("gui_base", file_id)
        if background and background.is_file():
            while not self.ready:
                time.sleep(1)
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
