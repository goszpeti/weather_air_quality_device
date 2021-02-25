"""
Entry module of PiWheater
Sets up cmd arguments, settings and starts the gui
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from piweather import __version__ as PIWHEATER_VERSION
from piweather import config
from piweather.base.component_ctrl import ComponentController
from piweather.base.logger import Logger
from piweather.base.system import RuntimeSystem
from piweather.resources import get_rsc_file
from piweather.settings import Settings
from piweather.ui import common, main_ui
from piweather.ui.widgets.splashscreen import SplashScreen
from piweather.ui.widgets.fader_widget import FaderWidget


# define Qt so we can use it like the namespace in C++
Qt = QtCore.Qt


def main(settings_path: Path = config.base_path):
    """
    Main function, calling setup, loading components and safe shutdown.
    param settings_path: only used for testing
    """

    # System is first, is_target_system is the most basic check

    # to be able to remote debug as much as possible, this call is being done early
    remote_debug()

    handle_cmd_args()
    runtime_system = RuntimeSystem()
    if not runtime_system.is_target_system:
        setup_on_non_target_system()

    settings = Settings(ini_folder=settings_path)
    # Set up global Qt Application instance
    config.qt_app = qt_app_setup(settings)

    comp_ctrl = ComponentController(settings)
    # main_ui must be held in this context, otherwise the gc will destroy the gui
    app_main_ui = loading_sequence(comp_ctrl, settings)  # pylint: disable=unused-variable

    logger = Logger()
    try:
        config.qt_app.exec_()
    except:  # pylint:disable=bare-except
        trace_back = traceback.format_exc()
        logger.error("Application crashed: \n%s", trace_back)

    # unload modules - wait for every thread to quit
    if runtime_system.is_target_system:
        logger.info("Prepare to exit...")
        if comp_ctrl:
            comp_ctrl.unload_all()
            while not comp_ctrl.all_unloaded:
                time.sleep(.1)


def handle_cmd_args():
    """
    All CLI related functions.
    """
    parser = argparse.ArgumentParser(
        prog="PiWheater", description="PiWeather commandline interface")
    parser.add_argument("-v", "--version", action="version",
                        version=PIWHEATER_VERSION)
    parser.parse_args()


def remote_debug():
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
    config.resource_path = config.base_path.parent / "resources"
    mockup_path = config.base_path.parent / "test/mock"
    Logger().info("System: Using mockups from %s", str(mockup_path))
    sys.path.append(str(mockup_path))


def qt_app_setup(settings) -> QtWidgets.QApplication:
    """
    Set up all Qt application specific attributes, which can't be changed later on
    Returns qt_app object.
    """
    logger = Logger()
    # apply Qt attributes (only at init possible)
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # start Qt app and ui
    qt_app = QtWidgets.QApplication([])

    # set icon
    icon_path = get_rsc_file("gui_base", "icon")
    qt_app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # set up font
    font_file = get_rsc_file("font", "weathericons")
    font_id = QtGui.QFontDatabase.addApplicationFont(str(font_file))
    if font_id != -1:
        font_db = QtGui.QFontDatabase()
        font_styles = font_db.styles(config.FONT_NAME)
        font_families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
        for font_family in font_families:
            font = font_db.font(font_family, font_styles[0], 13)
        qt_app.setFont(font)
    else:
        logger.warning("Can't apply selected font file.")

    # install translator
    common.set_ui_language(qt_app, settings)

    return qt_app


def loading_sequence(comp_ctrl: ComponentController, settings: Settings):
    """
    Load modules with watchdog and display Splashscreen until loading is finished.
    """
    # init speach module - this takes a while, so the output will be effectively heard,
    # when the splash screen is already loading. It is a non-blocking call.
    components = comp_ctrl.components
    components.tts.say_internal("startup", [PIWHEATER_VERSION])
    components.tts.wait_for_tts()

    # start init for all components
    comp_ctrl.init_all()
    app_main_ui = main_ui.WeatherMainUi(comp_ctrl, settings)

    is_target_system = RuntimeSystem().is_target_system
    if is_target_system:  # only remove titlebar on RPi
        app_main_ui.qt_root_obj.setWindowFlags(Qt.CustomizeWindowHint)

    # show splash screen
    movie_file = get_rsc_file("gui_base", "splash_spinner")
    movie = QtGui.QMovie(str(movie_file))
    splash_screen = SplashScreen(movie)
    splash_screen.show()

    # start gui init in separate qt thread
    thread = QtCore.QThread(app_main_ui)
    thread.started.connect(app_main_ui.init_gui)
    thread.start()

    # wait for finishing loading - processEvents is needed for animations to work (loader)
    loading_minimum_time = 10  # seconds
    start = time.time()
    while (not comp_ctrl.all_initialized or not app_main_ui.ready or not comp_ctrl.all_ready) \
            or (time.time() < start + loading_minimum_time):
        config.qt_app.processEvents()

    # splash screen can be disabled - with fader
    app_main_ui.qt_root_obj.show()
    fade_length = 1  # second
    fader_widget = FaderWidget(  # pylint: disable=unused-variable
        splash_screen, app_main_ui.qt_root_obj, length=fade_length*1000)
    splash_screen.finish(app_main_ui.qt_root_obj)
    return app_main_ui


if __name__ == "__main__":
    main()
