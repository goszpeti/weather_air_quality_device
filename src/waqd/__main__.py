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

import argparse
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from waqd import __version__ as WAQD_VERSION
from waqd import config
from waqd.assets import get_asset_file
from waqd.base.component_ctrl import ComponentController
from waqd.base.logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import (Settings, DISPLAY_TYPE, DISP_TYPE_HEADLESS, DISP_TYPE_WAVESHARE_EPAPER_2_9,
                           DISP_TYPE_WAVESHARE_5_LCD, DISP_TYPE_RPI)
from waqd.ui import common, main_ui
from waqd.ui.widgets.fader_widget import FaderWidget
from waqd.ui.widgets.splashscreen import SplashScreen

# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt


def handle_cmd_args(settings):
    """
    All CLI related functions.
    """
    parser = argparse.ArgumentParser(
        prog=config.PROG_NAME, description=f"{config.PROG_NAME} command line interface")
    parser.add_argument("-v", "--version", action="version",
                        version=WAQD_VERSION)
    parser.add_argument("-H", "--headless", action='store_true', dest='headless')
    parser.add_argument("-D", "--debug", type=int, default=config.DEBUG_LEVEL)

    args = parser.parse_args()
    config.DEBUG_LEVEL = args.debug
    if args.headless:
        settings.set(DISPLAY_TYPE, DISP_TYPE_HEADLESS)


def start_remote_debug():
    """ Start remote debugging from level 2 and wait on it from level 3"""
    runtime_system = RuntimeSystem()
    if config.DEBUG_LEVEL > 1 and runtime_system.is_target_system:
        import debugpy  # pylint: disable=import-outside-toplevel
        port = 3003
        debugpy.listen(("0.0.0.0", port))
        if config.DEBUG_LEVEL > 2:
            logger = Logger()
            logger.info("Waiting to attach on port %s", port)
            debugpy.wait_for_client()  # blocks execution until client is attached


def setup_on_non_target_system():
    """ Must be able to load on desktop systems """
    mockup_path = config.base_path.parent.parent / "test" / "mock"
    sys.path = [str(mockup_path)] + sys.path
    os.environ["PYTHONPATH"] = str(mockup_path) # for mh-z19
    config.user_config_dir = config.base_path.parent
    Logger().debug("System: Using mockups from %s" % str(mockup_path))  # don't use logger yet


def qt_app_setup(settings) -> QtWidgets.QApplication:
    """
    Set up all Qt application specific attributes, which can't be changed later on
    Returns qt_app object.
    """
    # apply Qt attributes (only at init possible)
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # set up global Qt Application instance
    qt_app = QtWidgets.QApplication([])

    # set icon
    icon_path = get_asset_file("gui_base", "icon")
    qt_app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # install translator
    common.set_ui_language(qt_app, settings)

    return qt_app


def loading_sequence(comp_ctrl: ComponentController, settings: Settings):
    """
    Load modules with watchdog and display Splashscreen until loading is finished.
    """
    # init speech module - this takes a while, so the output will be effectively heard,
    # when the splash screen is already loading. It is a non-blocking call.

    # start init for all components
    comp_ctrl.init_all()
    app_main_ui = main_ui.WeatherMainUi(comp_ctrl, settings)

    if RuntimeSystem().is_target_system:  # only remove titlebar on RPi
        app_main_ui.setWindowFlags(Qt.CustomizeWindowHint)

    # show splash screen
    splash_screen = SplashScreen()
    splash_screen.show()

    # start gui init in separate qt thread
    thread = QtCore.QThread(app_main_ui)
    thread.started.connect(app_main_ui.init_gui)
    thread.start()

    # wait for finishing loading - processEvents is needed for animations to work (loader)
    loading_minimum_time = 10  # seconds
    start = time.time()
    while (not app_main_ui.ready or not comp_ctrl.all_ready) \
        or (time.time() < start + loading_minimum_time) \
            and config.DEBUG_LEVEL <= 3:
        QtWidgets.QApplication.processEvents()

    # splash screen can be disabled - with fader
    app_main_ui.show()
    fade_length = 1  # second
    fader_widget = FaderWidget(  # pylint: disable=unused-variable
        splash_screen, app_main_ui, length=fade_length*1000)
    splash_screen.finish(app_main_ui)
    return app_main_ui


def main(settings_path: Optional[Path] = None):
    """
    Main function, calling setup, loading components and safe shutdown.
    :param settings_path: Only used for testing to load a settings file.
    """

    # Create user config dir
    if not config.user_config_dir.exists():
        os.makedirs(config.user_config_dir)

    Logger(output_path=config.user_config_dir)

    # System is first, is_target_system is the most basic check
    runtime_system = RuntimeSystem()
    if not runtime_system.is_target_system:
        setup_on_non_target_system()

    # All other classes depend on settings
    if not settings_path:
        settings_path = config.user_config_dir
    settings = Settings(ini_folder=settings_path)

    # to be able to remote debug as much as possible, this call is being done early
    start_remote_debug()
    handle_cmd_args(settings)

    comp_ctrl = ComponentController(settings)
    config.comp_ctrl = comp_ctrl

    comp_ctrl.components.tts.say_internal("startup", [WAQD_VERSION])
    display_type = settings.get(DISPLAY_TYPE)

    if display_type in [DISP_TYPE_RPI, DISP_TYPE_WAVESHARE_5_LCD]:
        config.qt_app = qt_app_setup(settings)
        # main_ui must be held in this context, otherwise the gc will destroy the gui
        loading_sequence(comp_ctrl, settings)
        try:
            config.qt_app.exec_()
        except:  # pylint:disable=bare-except
            trace_back = traceback.format_exc()
            Logger().error("Application crashed: \n%s", trace_back)
    elif display_type == DISP_TYPE_WAVESHARE_EPAPER_2_9:
        pass
    elif display_type == DISP_TYPE_HEADLESS:
        comp_ctrl.init_all()
        comp_ctrl._stop_event.wait()

    # unload modules - wait for every thread to quit
    if runtime_system.is_target_system:
        Logger().info("Prepare to exit...")
        if comp_ctrl:
            comp_ctrl.unload_all()
            while not comp_ctrl.all_unloaded:
                time.sleep(.1)


if __name__ == "__main__":
    main()
