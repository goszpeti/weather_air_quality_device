#!/bin/python3
# This script is being run as admin!

import logging
import os
import stat

from pathlib import Path

from installer.common import (
    INSTALL_TARGET_ROOT, AUTOSTART_FILE, USER_CONFIG_PATH, INSTALL_DIR_SUFFIX, LOCAL_BIN_PATH, USERNAME,
    installer_root_dir,
    add_to_autostart, get_waqd_version, get_waqd_bin_name, remove_from_autostart, set_write_permissions, setup_logger)

def install_waqd(waqd_version: str):
    logging.info("Installing with pipx")
    # use system-site-packages to use qt system package
    # -- suffix creates a version specific dir. "." will be converted to "-" in the name
    suffix = INSTALL_DIR_SUFFIX.format(version=waqd_version)
    # must be executed as user
    args = f"--force --verbose --system-site-packages --suffix {suffix} {installer_root_dir}"
    os.system(f'runuser - {USERNAME} -c "python3 -m pipx install {args}"')


def register_waqd_autostart(bin_path: Path = LOCAL_BIN_PATH, autostart_file: Path = AUTOSTART_FILE):
    # Create an executable with auto restart for the current user
    # TODO: This would be nicer? with systemctl -> Restart=on-failure..
    os.makedirs(bin_path, exist_ok=True)
    
    waqd_start_bin_path = bin_path / "waqd-start"
    waqd_bin_name = get_waqd_bin_name()
    waqd_bin_content = f"""#!/bin/bash
    until {waqd_bin_name}; do
        echo "WAQD crashed with exit code $?.  Respawning.." >&2
        sleep 1
    done
    """
    with open(waqd_start_bin_path, "w", encoding="utf-8") as fd:
        fd.write(waqd_bin_content)
    # chmod +x
    os.chmod(waqd_start_bin_path, os.stat(waqd_start_bin_path).st_mode | stat.S_IEXEC)
    os.system(f"chown {USERNAME} {waqd_start_bin_path}")
    logging.info(f"Add respawning {str(waqd_start_bin_path)} to autostart file {str(autostart_file)}")
    # first remove, to not aciddentally remove added lines
    remove_from_autostart(["waqd", "PiWeather"], autostart_file)
    add_to_autostart([str(waqd_start_bin_path)], autostart_file)

def do_install():
    # install and add to autostart
    set_write_permissions(INSTALL_TARGET_ROOT)
    install_waqd(get_waqd_version())

    register_waqd_autostart()
    # restart only if not in docker (for testing)
    ret = os.system("grep -q docker /proc/1/cgroup")
    if ret != 0:
        os.system("sudo reboot")
        logging.info("Restarting in one minute...")
