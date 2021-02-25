import logging
import os
import platform
import shutil
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from pathlib import Path

CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
ROOT_DIR = CURRENT_DIR.parent.parent
SRC_DIR = ROOT_DIR / "src"
RSC_DIR = ROOT_DIR / "resources"

# set up file logger - log everything in file and stdio
LOG_FORMAT = r"%(asctime)s :: %(levelname)s :: %(message)s"
LOG_DEBUG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_DEBUG_LEVEL,
                    filename=str(CURRENT_DIR / "piweather.log"),
                    format=LOG_FORMAT)
logging.getLogger().addHandler(logging.StreamHandler())

# determine path to installation
if platform.system() == "Linux":
    logging.info("Installing new version, please wait...")
    home = Path.home()
    install_path = home / "PiWeather"
    backup_path = home / ".PiWeather_old"

    logging.info("Backing up old installation")
    if install_path.exists() and os.listdir(install_path):
        if backup_path.exists():
            shutil.rmtree(backup_path, ignore_errors=True)
        os.makedirs(str(backup_path))
        copy_tree(str(install_path), str(backup_path))

    logging.info("Uninstalling old version")
    # delete old installation
    shutil.rmtree(str(install_path), ignore_errors=True)
    # create the install dir
    os.makedirs(str(install_path))

    if backup_path.exists():
        events_json = Path("/Nonexistant")
        for event in backup_path.rglob('events.json'):
            events_json = event
        if not events_json.exists():
            logging.warning("Cannot find events.json in old version")
        else:
            copy_file(str(events_json), str(install_path))

        config_ini = Path("/Nonexistant")
        for ini in backup_path.rglob('config.ini'):
            config_ini = ini
        if not config_ini.exists():
            logging.warning("Cannot find config.ini in old version")
        else:
            # place config_ini in new version dir - currently dst path is hardcoded
            copy_file(str(config_ini), str(install_path))

    logging.info("Copying files for new version...")
    # copy src and rsc
    copy_file(str(SRC_DIR / "main.py"), str(install_path / "main.py"))
    copy_tree(str(SRC_DIR / "piweather"), str(install_path / "piweather"))
    copy_tree(str(RSC_DIR), str(install_path / RSC_DIR.name))

    # start again
    os.system("sudo shutdown -r +1")
    logging.info("Restarting in one minute...")
