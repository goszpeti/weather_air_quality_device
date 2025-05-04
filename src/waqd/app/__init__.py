"""
Entry module of WAQD
Sets up cmd arguments, settings and starts the gui
"""

from typing import TYPE_CHECKING
import sys
import time
import traceback
from typing import Optional
from pint import UnitRegistry

import waqd
from waqd import __version__ as WAQD_VERSION
from waqd.base.component_ctrl import ComponentController
from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import (
    UI_TYPE,
    UI_TYPE_QT,
    UI_TYPE_WEB,
    Settings,
)

# don't import anything from Qt globally! we want to run also without qt in headless mode
if TYPE_CHECKING:
    from waqd.ui.qt.main_window import QtBackChannel
    from waqd.base.component_ctrl import ComponentController
    from PyQt5 import QtCore

    Qt = QtCore.Qt


# GLOBAL VARIABLES

# singleton with access to all backend components
comp_ctrl: ComponentController
# for global access to units
unit_reg = UnitRegistry()
# for global access to settings
settings: Settings

# Qt Stuff
# to send back data form backend to gui, if the gui loaded
qt_backchannel: Optional["QtBackChannel"] = None
# translator for qt app translation singleton
translator: Optional["QtCore.QTranslator"] = None
# for built-in Qt strings
base_translator: Optional["QtCore.QTranslator"] = None


def basic_setup():
    """
    Main function, calling setup, loading components and safe shutdown.
    :param settings_path: Only used for testing to load a settings file.
    """
    global comp_ctrl, settings

    sys.excepthook = crash_hook
    settings = Settings(ini_folder=waqd.user_config_dir)
    setup_unit_reg()

    # to be able to remote debug as much as possible, this call is being done early
    start_remote_debug()
    Logger(output_path=waqd.user_config_dir)  # singleton, no assigment needed
    if waqd.DEBUG_LEVEL > 0:
        Logger().info(f"DEBUG level set to {waqd.DEBUG_LEVEL}")

    if waqd.MIGRATE_SENSOR_LOGS:
        from waqd.base.file_logger import SensorFileLogger

        SensorFileLogger.migrate_txts_to_db()
        return None, None
    comp_ctrl = ComponentController(settings)
    if waqd.DEBUG_LEVEL > 1:  # disable startup sound
        comp_ctrl.components.tts.say_internal("startup", [WAQD_VERSION])


def main():
    basic_setup()
    global comp_ctrl, settings
    if not comp_ctrl or not settings:
        return
    # Load the selected GUI mode
    display_type = settings.get(UI_TYPE)
    try:
        comp_ctrl.init_all()
        if waqd.HEADLESS_MODE:
            comp_ctrl._stop_event.wait()

        elif display_type == UI_TYPE_QT:
            comp_ctrl.init_all()
            from waqd.ui.qt.startup import qt_app_setup, qt_loading_sequence

            qt_app = qt_app_setup()
            # main_ui must be held in this context, otherwise the gc will destroy the gui
            qt_loading_sequence(comp_ctrl)
            qt_app.exec()
        elif display_type == UI_TYPE_WEB:
            from waqd.ui.web2 import (
                start_web_browser,
                start_web_server,
                start_web_ui_chromium_kiosk_mode,
            )

            runtime_system = RuntimeSystem()
            if runtime_system.is_target_system:
                start_web_ui_chromium_kiosk_mode()
            else:
                start_web_browser()
            start_web_server(waqd.DEBUG_LEVEL > 0)
            comp_ctrl._stop_event.wait()

    except Exception:
        trace_back = traceback.format_exc()
        Logger().error("Application crashed: \n%s", trace_back)

    # unload modules - wait for every thread to quit
    Logger().info("Prepare to exit...")
    if comp_ctrl:
        comp_ctrl.unload_all()
        while not comp_ctrl.all_unloaded:
            time.sleep(0.1)


def start_remote_debug():
    """Start remote debugging from level 2 and wait on it from level 3"""
    runtime_system = RuntimeSystem()
    if waqd.DEBUG_LEVEL > 1 and runtime_system.is_target_system:
        import debugpy  # pylint: disable=import-outside-toplevel

        port = 3003
        debugpy.listen(("0.0.0.0", port))
        if waqd.DEBUG_LEVEL > 2:
            print("Waiting to attach on port %s", port)
            debugpy.wait_for_client()  # blocks execution until client is attached


def setup_unit_reg():
    """Setup custom units"""
    unit_reg.define("fraction = [] = frac")
    unit_reg.define("percent = 1e-2 frac = %")
    unit_reg.define("ppm = 1e-6 fraction")
    unit_reg.define("ppb = 1e-9 fraction")


def crash_hook(exctype, excvalue, tb):
    try:
        tb_formatted = "\n".join(traceback.format_tb(tb, limit=10))
        error_text = f"Application crashed: {str(exctype)} {excvalue}\n{tb_formatted}"
        Logger().fatal(error_text)
    except Exception:  # just in case, otherwise we get an endless exception loop
        sys.exit(2)
    sys.exit(1)
