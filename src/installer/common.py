#!/bin/python3
# This script is being run as admin!

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Union, Literal


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


def setup_logger(log_file: Path):
    # set up file logger - log everything in file and stdio
    logging.basicConfig(level=logging.DEBUG,
                        filename=str(log_file),
                        format=r"%(asctime)s :: %(levelname)s :: %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def set_write_permissions(path: Path):
    os.system(f"sudo chmod ugo+rwx {str(path)}")
    os.system(f"sudo chown {USERNAME} {str(path)}")


def get_waqd_install_path(package_root_dir: Path = installer_root_dir) -> Path:
    # determine path to installation
    dir_name = get_waqd_bindir_name(package_root_dir)
    install_path = INSTALL_TARGET_ROOT / dir_name
    return install_path


def get_waqd_bindir_name(package_root_dir: Path = installer_root_dir) -> str:
    waqd_version = get_waqd_version(package_root_dir)
    # replace . with - (pipx does this)
    suffix = INSTALL_DIR_SUFFIX.format(version=waqd_version).replace(".", "-")
    return "waqd" + suffix


def get_waqd_bin_name(package_root_dir: Path = installer_root_dir) -> str:
    waqd_version = get_waqd_version(package_root_dir)
    suffix = INSTALL_DIR_SUFFIX.format(version=waqd_version)
    return "waqd" + suffix


def get_waqd_version(package_root_dir: Path = installer_root_dir) -> str:
    """ Determine version from config file - need to read it manually,
    # importing is not possible without dependencies """
    about: Dict[str, str] = {}
    version = "latest"
    try:
        sys.path.insert(0, os.path.join(package_root_dir, "src"))
        import waqd
        version = waqd.__version__
    except Exception as e:
        logging.error(str(e))
    return version


def assure_file_exists(file_path: Path, chown=True):
    """ Create dirs, add to current user and create file. Returns True if file existed before. """
    if file_path.exists():
        return True
    logging.info(f"Cannot find file {str(file_path)}- creating it")
    os.makedirs(file_path.parent, exist_ok=True)
    if chown:
        (f"sudo chown {USERNAME} {str(file_path.parent)}")
    file_path.touch(exist_ok=True)
    return False


def assure_file_does_not_exist(file_path: Path, chown=True):
    """ Create dirs, add to current user and create file. Returns True if file did not exist. """
    if not file_path.exists():
        return True
    logging.info(f"File {str(file_path)} exists - deleting it")
    if chown:
        (f"sudo chown {USERNAME} {str(file_path.parent)}")
    os.remove(file_path)
    return False


def replace_in_file(search_replace: Dict[str, str], file_path: Path):
    """ Replace exact entries in file"""
    assure_file_exists(file_path)
    text = file_path.read_text()
    for search, replace in search_replace.items():
        text = text.replace(search, replace)
    file_path.write_text(text)


def remove_line_in_file(remove_lines: List[str], file_path: Path):
    """ Remove lines in file """
    assure_file_exists(file_path)
    with open(file_path, "r+") as fd:
        lines = fd.readlines()
        fd.seek(0)
        fd.truncate()
        new_entries = []
        for line in lines:
            if not any(remove_line in line for remove_line in remove_lines):
                new_entries.append(line)
        fd.writelines(new_entries)


def add_line_to_file(lines_to_add: List[str], file_path: Path, unique=True):
    """ Add lines to file, unqiue to check, if it should appear only once """
    assure_file_exists(file_path)
    with open(file_path, "r+") as fd:
        entries = fd.readlines()
        for line_to_add in lines_to_add:
            if not unique:
                fd.write(f"{line_to_add}\n")
                break
            if line_to_add + "\n" not in entries:
                fd.write(f"{line_to_add}\n")


def comment_line_in_file(line_to_comment: str, file_path: Path, comment_char="#", uncomment=False):
    text = file_path.read_text()
    new_text = ""
    for line in text.splitlines():
        if line_to_comment in line:
            if uncomment:
                line.replace(comment_char, "")
            else:
                line = comment_char + " " + line
        new_text += line + "\n"

    file_path.write_text(new_text)


def add_to_autostart(cmds_to_add: List[str], autostart_file: Path = AUTOSTART_FILE):
    """ Uses LXDE autostart file and format """
    lines_to_add = []
    for cmd_to_add in cmds_to_add:
        if not cmd_to_add.startswith("@"):
            lines_to_add.append("@" + cmd_to_add)
    add_line_to_file(lines_to_add, autostart_file)


def remove_from_autostart(remove_items: List[str] = [], autostart_file: Path = AUTOSTART_FILE):
    """ Uses LXDE autostart file and format """
    remove_line_in_file(remove_items, autostart_file)
