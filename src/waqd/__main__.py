import argparse
import os
import sys
import waqd

def setup_on_non_target_system():
    """Must be able to load on desktop systems"""
    mockup_path = waqd.base_path.parent.parent / "test" / "mock"
    sys.path = [str(mockup_path)] + sys.path
    os.environ["PYTHONPATH"] = str(mockup_path)  # for mh-z19
    waqd.user_config_dir = waqd.base_path.parent
    import logging

    logging.getLogger("root").info(
        "System: Using mockups from %s" % str(mockup_path)
    )  # don't use logger yet


def parse_cmd_args():
    """
    All CLI related functions.
    """

    parser = argparse.ArgumentParser(
        prog=waqd.PROG_NAME, description=f"{waqd.PROG_NAME} command line interface"
    )
    parser.add_argument("-v", "--version", action="version", version=waqd.__version__)
    parser.add_argument("-H", "--headless", action="store_true")
    parser.add_argument("-D", "--debug_level", type=int, default=waqd.DEBUG_LEVEL)
    parser.add_argument("-M", "--migrate_sensor_logs", action="store_true")

    args = parser.parse_args()
    waqd.DEBUG_LEVEL = args.debug_level
    debug_env_var = os.getenv("WAQD_DEBUG")
    if debug_env_var:
        waqd.DEBUG_LEVEL = int(debug_env_var)
    if args.headless:
        waqd.HEADLESS_MODE = True
    if args.migrate_sensor_logs:
        waqd.MIGRATE_SENSOR_LOGS = True


def startup():
    # System is first, is_target_system is the most basic check
    from waqd.base.system import RuntimeSystem

    runtime_system = RuntimeSystem()
    if not runtime_system.is_target_system:
        setup_on_non_target_system()

    parse_cmd_args()  # cmd args set Debug level for logger
    from waqd.app import main

    main()


if __name__ == "__main__":
    startup()
