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
Entry module of WAQD
Sets up cmd arguments, settings and starts the gui
"""

 
from typing import TYPE_CHECKING
import argparse
import logging
import os
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Optional
from pint import UnitRegistry

import waqd
from waqd import PROG_NAME
from waqd import __version__ as WAQD_VERSION
from waqd import base_path
from waqd.assets import get_asset_file
from waqd.base.component_ctrl import ComponentController
from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import (DISP_TYPE_RPI,
                           DISP_TYPE_WAVESHARE_5_LCD,
                           DISP_TYPE_WAVESHARE_EPAPER_2_9, DISPLAY_TYPE, FONT_NAME,
                           FONT_SCALING,
                           Settings)

# don't import anything from Qt globally! we want to run also without qt in headless mode
if TYPE_CHECKING:
    from waqd.base.component_ctrl import ComponentController
    from PyQt5 import QtCore, QtWidgets
    Qt = QtCore.Qt


# GLOBAL VARIABLES

# singleton with access to all backend components
comp_ctrl: Optional["ComponentController"] = None
# translator for qt app translation singleton
translator: Optional["QtCore.QTranslator"] = None
unit_reg = UnitRegistry()

def main(settings_path: Optional[Path] = None):
    """
    Main function, calling setup, loading components and safe shutdown.
    :param settings_path: Only used for testing to load a settings file.
    """
    sys.excepthook = crash_hook

    # Create user config dir
    if not waqd.user_config_dir.exists():
        os.makedirs(waqd.user_config_dir)

    # System is first, is_target_system is the most basic check
    runtime_system = RuntimeSystem()
    if not runtime_system.is_target_system:
        setup_on_non_target_system()

    # All other classes depend on settings
    if not settings_path:
        settings_path = waqd.user_config_dir
    settings = Settings(ini_folder=settings_path)

    parse_cmd_args(settings)  # cmd args set Debug level for logger

    # to be able to remote debug as much as possible, this call is being done early
    start_remote_debug()
    Logger(output_path=waqd.user_config_dir)  # singleton, no assigment needed
    if waqd.DEBUG_LEVEL > 0:
        Logger().info(f"DEBUG level set to {waqd.DEBUG_LEVEL}")

    if waqd.MIGRATE_SENSOR_LOGS:
        from waqd.base.file_logger import SensorFileLogger
        SensorFileLogger.migrate_txts_to_db()
        return
    global comp_ctrl
    comp_ctrl = ComponentController(settings)
    if waqd.DEBUG_LEVEL > 1: # disable startup sound
       comp_ctrl.components.tts.say_internal("startup", [WAQD_VERSION])
    comp_ctrl.init_all()
    # Load the selected GUI mode
    display_type = settings.get(DISPLAY_TYPE)
    try:
        if waqd.HEADLESS_MODE:
            comp_ctrl._stop_event.wait()
        elif display_type in [DISP_TYPE_RPI, DISP_TYPE_WAVESHARE_5_LCD]:
            qt_app = qt_app_setup(settings)
            # main_ui must be held in this context, otherwise the gc will destroy the gui
            qt_loading_sequence(comp_ctrl, settings)
            qt_app.exec()
        elif display_type == DISP_TYPE_WAVESHARE_EPAPER_2_9:
            pass
    except:  # pylint:disable=bare-except
            trace_back = traceback.format_exc()
            Logger().error("Application crashed: \n%s", trace_back)

    # unload modules - wait for every thread to quit
    # if runtime_system.is_target_system:
    Logger().info("Prepare to exit...")
    if comp_ctrl:
        comp_ctrl.unload_all()
        while not comp_ctrl.all_unloaded:
            time.sleep(.1)


def parse_cmd_args(settings):
    """
    All CLI related functions.
    """
    parser = argparse.ArgumentParser(
        prog=PROG_NAME, description=f"{PROG_NAME} command line interface")
    parser.add_argument("-v", "--version", action="version",
                        version=WAQD_VERSION)
    parser.add_argument("-H", "--headless", action='store_true')
    parser.add_argument("-D", "--debug_level", type=int, default=waqd.DEBUG_LEVEL)
    parser.add_argument("-M", "--migrate_sensor_logs", action='store_true')

    args = parser.parse_args()
    waqd.DEBUG_LEVEL = args.debug_level
    debug_env_var = os.getenv("WAQD_DEBUG")
    if debug_env_var:
        waqd.DEBUG_LEVEL = int(debug_env_var)
    if args.headless:
        waqd.HEADLESS_MODE = True
    if args.migrate_sensor_logs:
        waqd.MIGRATE_SENSOR_LOGS = True

def start_remote_debug():
    """ Start remote debugging from level 2 and wait on it from level 3"""
    runtime_system = RuntimeSystem()
    if waqd.DEBUG_LEVEL > 1 and runtime_system.is_target_system:
        import debugpy  # pylint: disable=import-outside-toplevel
        port = 3003
        debugpy.listen(("0.0.0.0", port))
        if waqd.DEBUG_LEVEL > 2:
            print("Waiting to attach on port %s", port)
            debugpy.wait_for_client()  # blocks execution until client is attached


def setup_on_non_target_system():
    """ Must be able to load on desktop systems """
    mockup_path = base_path.parent.parent / "test" / "mock"
    sys.path = [str(mockup_path)] + sys.path
    os.environ["PYTHONPATH"] = str(mockup_path)  # for mh-z19
    waqd.user_config_dir = base_path.parent
    logging.getLogger("root").info("System: Using mockups from %s" % str(mockup_path))  # don't use logger yet


def qt_app_setup(settings: Settings) -> "QtWidgets.QApplication":
    """
    Set up all Qt application specific attributes, which can't be changed later on
    Returns qt_app object.
    """
    from PyQt5 import QtCore, QtGui, QtWidgets
    Qt = QtCore.Qt
    if platform.system() == "Windows":
        # Workaround for Windows, so that on the taskbar the
        # correct icon will be shown (and not the default python icon).
        from PyQt5.QtWinExtras import QtWin
        MY_APP_ID = 'ConanAppLauncher.' + WAQD_VERSION
        QtWin.setCurrentProcessExplicitAppUserModelID(MY_APP_ID)


    # apply Qt attributes (only at init possible)
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # set up global Qt Application instance
    qt_app = QtWidgets.QApplication([])
    # set icon
    icon_path = get_asset_file("gui_base", "icon")
    qt_app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    from waqd.ui.qt.common import set_ui_language

    # install translator
    set_ui_language(qt_app, settings)
    from waqd.ui.qt.theming import activate_theme
    activate_theme(settings.get_float(FONT_SCALING), settings.get_string(FONT_NAME))

    return qt_app


def qt_loading_sequence(comp_ctrl: ComponentController, settings: Settings):
    """
    Load modules with watchdog and display Splashscreen until loading is finished.
    """
    # init speech module - this takes a while, so the output will be effectively heard,
    # when the splash screen is already loading. It is a non-blocking call.

    # start init for all components
    from PyQt5 import QtCore, QtWidgets
    from waqd.ui.qt.main_ui import WeatherMainUi
    from waqd.ui.qt.widgets.fader_widget import FaderWidget
    from waqd.ui.qt.widgets.splashscreen import SplashScreen
    # show splash screen
    splash_screen = SplashScreen()
    splash_screen.show()

    # wait for finishing loading - processEvents is needed for animations to work (loader)
    loading_minimum_time_s = 5
    start = time.time()
    while not comp_ctrl.all_ready:
        QtWidgets.QApplication.processEvents()

    # start gui init in separate qt thread
    app_main_ui = WeatherMainUi(comp_ctrl, settings)

    if RuntimeSystem().is_target_system:  # only remove titlebar on RPi
        app_main_ui.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
    thread = QtCore.QThread(app_main_ui)
    thread.started.connect(app_main_ui.init_gui)
    thread.start()
    while (not app_main_ui.ready) \
        or (time.time() < start + loading_minimum_time_s) \
            and waqd.DEBUG_LEVEL <= 3:
        QtWidgets.QApplication.processEvents()


    # splash screen can be disabled - with fader
    app_main_ui.show()
    fade_length = 1  # second
    fader_widget = FaderWidget(  # pylint: disable=unused-variable
        splash_screen, app_main_ui, length=fade_length*1000)
    splash_screen.finish(app_main_ui)
    return app_main_ui


def crash_hook(exctype, excvalue, tb):
    try:
        tb_formatted = "\n".join(traceback.format_tb(tb, limit=10))
        error_text = f"Application crashed: {str(exctype)} {excvalue}\n{tb_formatted}"
        Logger().fatal(error_text)
    except:  # just in case, otherwise we get an endless exception loop
        sys.exit(2)
    sys.exit(1)
