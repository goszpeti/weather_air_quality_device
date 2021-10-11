#!/bin/python3
# This script is being run as admin!

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict


USERNAME = os.environ.get("SUDO_USER", "")  # the original user
if not USERNAME:
    USERNAME = os.environ.get("USER", "pi")
HOME = Path("/home") / USERNAME

LOCAL_BIN_PATH = HOME / ".local" / "bin"
INSTALL_TARGET_ROOT = HOME / ".local" / "pipx" / "venvs"
USER_CONFIG_PATH = HOME / ".waqd"
AUTOSTART_FILE = HOME / ".config/lxsession/LXDE-pi/autostart"

INSTALL_DIR_SUFFIX = ".{version}"

current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
installer_root_dir = current_dir.parent.parent


def setup_logger(file_dir: Path):
    # set up file logger - log everything in file and stdio
    logging.basicConfig(level=logging.DEBUG,
                        filename=str(file_dir / "waqd_install.log"),
                        format=r"%(asctime)s :: %(levelname)s :: %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def set_write_premissions(path: Path):
    os.makedirs(path, exist_ok=True)
    os.system(f"chmod ugo+rwx {path}") # TODO can this fail if path does not exist?


def get_waqd_install_path(package_root_dir: Path = installer_root_dir) -> Path:
    # determine path to installation
    dir_name = get_waqd_bin_name(package_root_dir)
    install_path = INSTALL_TARGET_ROOT / dir_name
    return install_path


def get_waqd_bin_name(package_root_dir: Path = installer_root_dir) -> str:
    waqd_version = get_waqd_version(package_root_dir)
    # replace . with - (pipx does this)
    suffix = INSTALL_DIR_SUFFIX.format(version=waqd_version).replace(".", "-")
    return "waqd" + suffix


def get_waqd_version(package_root_dir: Path = installer_root_dir) -> str:
    """ Determine version from config file - need to read it manually,
    # importing is not possible without dependencies """
    about: Dict[str, str] = {}
    with open(os.path.join(package_root_dir, "src", "waqd", '__init__.py')) as fd:
        exec(fd.read(), about)  # pylint: disable=exec-used
    return about["__version__"]


def add_to_autostart(cmd_to_add: str, remove_items: List[str] = [], autostart_file: Path = AUTOSTART_FILE):
    """ Uses LXDE autostart file and format """
    os.makedirs(autostart_file.parent, exist_ok=True)
    # append the current cmd to remove items- we don't want it twice
    remove_items.append(cmd_to_add)
    autostart_file.touch(exist_ok=True)
    with open(autostart_file, "r+") as fd:
        entries = fd.readlines()
        # delete all entries in the file
        fd.seek(0)
        fd.truncate()
        new_entries = []
        # remove lxpanel --profile entry and legacy entries
        for entry in entries:
            if not any(remove_entry in entry for remove_entry in remove_items):
                new_entries.append(entry)
        # add new entry
        new_entries.append(f"@{cmd_to_add}\n")
        fd.writelines(new_entries)
