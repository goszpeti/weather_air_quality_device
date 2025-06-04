import configparser
import logging
import os
import secrets
from pathlib import Path
from typing import Union, Dict
from waqd import PROG_NAME
from waqd.settings import (
    AUTO_UPDATER_ENABLED,
    CCS811_ENABLED,
    FORECAST_BG,
    INTERIOR_BG,
    LOCATION_ALTITUDE_M,
    LAST_TEMP_C_OUTSIDE,
    LOCATION_COUNTRY_CODE,
    LOCATION_STATE,
    MH_Z19_ENABLED,
    AW_API_KEY,
    EVENTS_ENABLED,
    BRIGHTNESS,
    DAY_STANDBY_TIMEOUT,
    DISP_TYPE_RPI,
    DISPLAY_TYPE,
    LANG,
    MH_Z19_VALUE_OFFSET,
    LOCATION_LONGITUDE,
    LOCATION_LATITUDE,
    REMOTE_API_KEY,
    REMOTE_MODE_URL,
    STARTUP_JINGLE,
    UPDATER_USER_BETA_CHANNEL,
    LANG_GERMAN,
    LOCATION_NAME,
    MOTION_SENSOR_ENABLED,
    MOTION_SENSOR_PIN,
    NIGHT_MODE_BEGIN,
    NIGHT_MODE_END,
    NIGHT_STANDBY_TIMEOUT,
    OW_API_KEY,
    SOUND_ENABLED,
    DHT_22_PIN,
    BME_280_ENABLED,
    BMP_280_ENABLED,
    USER_API_KEY,
    USER_SESSION_SECRET,
    USER_DEFAULT_PW,
    WAVESHARE_DISP_BRIGHTNESS_PIN,
    DHT_22_DISABLED,
    LOG_SENSOR_DATA,
)

def strtobool(value: str) -> bool:
    value = value.lower()
    if value in ("y", "yes", "on", "1", "true", "t"):
        return True
    return False

class Settings:
    """
    Settings mechanism with an ini file to use as a storage.
    File and entries are automatically created form the default value of the entry.
    """

    # internal constants
    _THEMING_SECTION_NAME = "GUI"
    _GENERAL_SECTION_NAME = "General"
    _ENERGY_SECTION_NAME = "Energy"
    _LOCATION_SECTION_NAME = "Location"
    _REMOTE_SECTION_NAME = "User"
    _SENSOR_SECTION_NAME = "Sensors"
    _SECRET_SECTION_NAME = "Secrets"

    def __init__(self, ini_folder=None, auto_save=True):
        """
        Read waqd.ini file to load settings.
        Verify waqd.ini existence, if folder is passed.
        """
        self._logger = logging.getLogger(PROG_NAME)
        self._parser = configparser.ConfigParser()
        self._ini_file_path = Path()
        if ini_folder is not None:
            self._ini_file_path = Path(ini_folder) / "config.ini"
        # create Settings ini file, if not available for first start
        if not self._ini_file_path.is_file():
            os.makedirs(self._ini_file_path.parent, exist_ok=True)
            self._ini_file_path.open("a").close()
            self._logger.warning("Settings: Creating settings ini-file")
        else:
            self._logger.info("Settings: Using %s", str(self._ini_file_path))
        self._auto_save = auto_save

        ### default setting values ###
        self._values = {
            self._GENERAL_SECTION_NAME: {
                LANG: LANG_GERMAN,
                SOUND_ENABLED: False,
                EVENTS_ENABLED: True,
                DISPLAY_TYPE: DISP_TYPE_RPI,
                WAVESHARE_DISP_BRIGHTNESS_PIN: 18,
                AUTO_UPDATER_ENABLED: True,
                UPDATER_USER_BETA_CHANNEL: False,
                LAST_TEMP_C_OUTSIDE: 23.5,
                STARTUP_JINGLE: True,
            },
            self._THEMING_SECTION_NAME: {
                INTERIOR_BG: "background_s8.jpg",
                FORECAST_BG: "background_s9.jpg",
            },
            self._ENERGY_SECTION_NAME: {
                NIGHT_MODE_BEGIN: "22:00",
                NIGHT_MODE_END: "07:00",
                BRIGHTNESS: 90,
                DAY_STANDBY_TIMEOUT: 600,
                NIGHT_STANDBY_TIMEOUT: 600,
            },
            self._LOCATION_SECTION_NAME: {
                LOCATION_NAME: "",
                LOCATION_COUNTRY_CODE: "",
                LOCATION_LATITUDE: 0.0,
                LOCATION_LONGITUDE: 0.0,
                LOCATION_ALTITUDE_M: 400.0,
                LOCATION_STATE: "",
                OW_API_KEY: "",
                AW_API_KEY: "",
            },
            self._REMOTE_SECTION_NAME: {
                REMOTE_MODE_URL: "",
                REMOTE_API_KEY: "",
            },
            self._SENSOR_SECTION_NAME: {
                DHT_22_PIN: DHT_22_DISABLED,  # if not disabled, the pin number is used
                BME_280_ENABLED: False,
                BMP_280_ENABLED: False,
                CCS811_ENABLED: False,
                MH_Z19_ENABLED: False,
                MH_Z19_VALUE_OFFSET: 0,
                MOTION_SENSOR_ENABLED: True,
                MOTION_SENSOR_PIN: 23,
                LOG_SENSOR_DATA: True,
            },
            self._SECRET_SECTION_NAME: {
                USER_SESSION_SECRET: secrets.token_hex(32),
                USER_API_KEY: "",
                USER_DEFAULT_PW: secrets.token_hex(32),
            },
        }

        self._read_ini()

    def get(self, name: str) -> Union[str, int, float, bool, Dict[str, str]]:
        """Get a specific setting"""
        value = None
        for section in self._values.values():
            if name in section:
                value = section.get(name)
                break
        if value is None:
            raise LookupError
        return value

    def get_string(self, name: str) -> str:
        return str(self.get(name))

    def get_int(self, name: str) -> int:
        return int(self.get(name))  # type: ignore

    def get_float(self, name: str) -> float:
        return float(self.get(name))  # type: ignore

    def get_bool(self, name: str) -> bool:
        return bool(self.get(name))

    def set(self, setting_name: str, value: Union[str, int, float, bool]):
        """Set the value of a specific setting. Does not write to file, if value is already set."""
        for section in self._values.keys():
            if setting_name in self._values[section]:
                if self._values[section][setting_name] == value:
                    return
                # cast to current type
                current_value = self._values[section][setting_name]
                if isinstance(value, str):
                    if isinstance(current_value, bool):
                        # strtobool returns 1 or 0, so we convert it to bool
                        value = bool(strtobool(value))
                    elif isinstance(current_value, str):
                        value = str(value)
                    elif isinstance(current_value, float):
                        value = float(value)
                    elif isinstance(current_value, int):
                        value = int(value)

                self._values[section][setting_name] = value
                # self._logger.debug("Settings: Set %s to %s", setting_name, value)
                break
        if self._auto_save:
            self._logger.debug("Settings: Auto-saving settings")
            self.save()

    def get_all(self) -> Dict[str, Union[str, int, float, bool]]:
        """Get all settings without sections and secrets as a dictionary."""
        all_settings = {}
        for section, options in self._values.items():
            if section == self._SECRET_SECTION_NAME:
                continue
            for option, value in options.items():
                all_settings[option] = value
        return all_settings

    def save(self):
        """Save all user modifiable options to file."""
        for section in self._values:
            for option in self._values[section]:
                self._write_setting(option, section)

        with self._ini_file_path.open("w", encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _read_ini(self):
        """Read settings ini with configparser."""
        update_needed = False
        try:
            self._parser.read(self._ini_file_path, encoding="UTF-8")
            for section in self._values.keys():
                for setting in self._values[section]:
                    update_needed |= self._read_setting(setting, section)
        except Exception as e:
            self._logger.error("Settings: Can't read ini file: %s, trying to delete...", str(e))
            os.remove(
                str(self._ini_file_path)
            )  # let an exeception to the user, file can't be deleted

        # write file - to record defaults, if missing
        if not update_needed:
            return
        with self._ini_file_path.open("w", encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _get_section(self, section_name):
        """Helper function to get a section from ini, or create it, if it does not exist."""
        if section_name not in self._parser:
            self._parser.add_section(section_name)
        return self._parser[section_name]

    def _read_setting(self, setting_name: str, section_name: str) -> bool:
        """Helper function to get a setting, which uses the init value to determine the type.
        Returns, if file needs tobe updated
        """
        section = self._get_section(section_name)
        default_value = self.get(setting_name)
        if isinstance(default_value, dict):  # no dicts supported directly
            return False
        if setting_name not in section:  # write out
            section[setting_name] = str(default_value)
            return True

        value = None
        if isinstance(default_value, bool):
            value = section.getboolean(setting_name)
        elif isinstance(default_value, str):
            value = section.get(setting_name)
        elif isinstance(default_value, float):
            value = float(section.get(setting_name, 0))
        elif isinstance(default_value, int):
            value = int(section.get(setting_name, 0))
        if value is None:
            self._logger.error("Settings: Setting %s is unknown", setting_name)
            return False
        # autosave must be disabled, otherwise we overwrite the other settings in the file
        auto_save = self._auto_save
        self._auto_save = False
        self.set(setting_name, value)
        self._auto_save = auto_save
        return False

    def _write_setting(self, option_name, section_name):
        """Helper function to write an option."""
        value = self.get(option_name)
        section = self._get_section(section_name)
        if not option_name in section:
            self._logger.error("Option %s to write is unknown", option_name)
        if isinstance(value, dict):
            # dicts are handled as ordered dicts, where one line is one entry named option_name + _<id>
            # Values are the key-value pairs separated with ","
            i = 0
            for key, value in value.items():
                section[option_name + "_" + str(i)] = key + "," + value
                i += 1
            return
        else:
            section[option_name] = str(value)
