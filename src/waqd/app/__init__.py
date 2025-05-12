"""
Entry module of WAQD
Sets up cmd arguments, settings and starts the gui
"""

from typing import TYPE_CHECKING
import sys
import time

import waqd
from waqd import __version__ as WAQD_VERSION
from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem

# don't import anything from Qt globally! we want to run also without qt in headless mode
if TYPE_CHECKING:
    from waqd.base.component_ctrl import ComponentController
    from pint import UnitRegistry
    from waqd.settings import Settings

# GLOBAL VARIABLES

# singleton with access to all backend components
comp_ctrl: "ComponentController"
# for global access to units
unit_reg: "UnitRegistry"
# for global access to settings
settings: "Settings"


def basic_setup():
    """
    Main function, calling setup, loading components and safe shutdown.
    :param settings_path: Only used for testing to load a settings file.
    """
    global comp_ctrl, settings

    sys.excepthook = crash_hook

    from waqd.settings import Settings

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
    from waqd.base.component_ctrl import ComponentController

    comp_ctrl = ComponentController(settings)
    if waqd.DEBUG_LEVEL > 1:  # disable startup sound
        comp_ctrl.components.tts.say_internal("startup", [WAQD_VERSION])


def main():
    basic_setup()
    global comp_ctrl, settings
    if not comp_ctrl or not settings:
        return
    # Load the selected GUI mode
    try:
        comp_ctrl.init_all()
        from waqd.ui.web2 import (
            start_web_server,
            start_web_ui_chromium_kiosk_mode,
        )

        runtime_system = RuntimeSystem()
        if runtime_system.is_target_system and not waqd.HEADLESS_MODE:
            start_web_ui_chromium_kiosk_mode()

        start_web_server(reload=waqd.DEBUG_LEVEL > 3)
        comp_ctrl._stop_event.wait()

    except Exception:
        import traceback

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
    global unit_reg
    from pint import UnitRegistry

    unit_reg = UnitRegistry()

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
