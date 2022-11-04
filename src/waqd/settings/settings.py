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
import configparser
import logging
import os
import bcrypt
from pathlib import Path
from typing import Union, Dict

from waqd.settings import (ALLOW_UNATTENDED_UPDATES, AUTO_UPDATER_ENABLED,
                           CCS811_ENABLED, FORECAST_BG, INTERIOR_BG, LAST_ALTITUDE_M_VALUE, LAST_TEMP_C_OUTSIDE_VALUE, MH_Z19_ENABLED, AW_API_KEY, EVENTS_ENABLED, FONT_NAME,
                           AW_CITY_IDS, BRIGHTNESS, DAY_STANDBY_TIMEOUT, DISP_TYPE_RPI,
                           DISPLAY_TYPE, FONT_SCALING, FORECAST_ENABLED, LANG, MH_Z19_VALUE_OFFSET, REMOTE_MODE_URL, UPDATER_USER_BETA_CHANNEL,
                           LANG_GERMAN, LOCATION, MOTION_SENSOR_ENABLED, MOTION_SENSOR_PIN,
                           NIGHT_MODE_BEGIN, NIGHT_MODE_END, NIGHT_STANDBY_TIMEOUT, OW_API_KEY,
                           OW_CITY_IDS, PREFER_ACCU_WEATHER, SOUND_ENABLED, DHT_22_PIN, BME_280_ENABLED, BMP_280_ENABLED, USER_API_KEY, USER_SESSION_SECRET,
                           WAVESHARE_DISP_BRIGHTNESS_PIN, DHT_22_DISABLED, LOG_SENSOR_DATA, SERVER_ENABLED)


class Settings():
    """
    Settings mechanism with an ini file to use as a storage.
    File and entries are automatically created form the default value of the entry.
    """

    # internal constants
    _GUI_SECTION_NAME = "GUI"
    _GENERAL_SECTION_NAME = "General"
    _FORECAST_SECTION_NAME = "Forecast"
    _ENERGY_SECTION_NAME = "Energy"

    def __init__(self, ini_folder=None, auto_save=True):
        """
        Read waqd.ini file to load settings.
        Verify waqd.ini existence, if folder is passed.
        """
        self._logger = logging.getLogger("root")
        self._parser = configparser.ConfigParser()
        self._ini_file_path = Path()
        if ini_folder is not None:
            self._ini_file_path = Path(ini_folder) / "config.ini"
        # create Settings ini file, if not available for first start
        if not self._ini_file_path.is_file():
            os.makedirs(self._ini_file_path.parent, exist_ok=True)
            self._ini_file_path.open('a').close()
            self._logger.warning('Settings: Creating settings ini-file')
        else:
            self._logger.info('Settings: Using %s', self._ini_file_path)
        self._auto_save = auto_save

        ### default setting values ###
        self._values = {
            self._GENERAL_SECTION_NAME: {
                LANG: LANG_GERMAN,
                SOUND_ENABLED: False,
                EVENTS_ENABLED: True,
                DISPLAY_TYPE: DISP_TYPE_RPI,
                CCS811_ENABLED: False,
                MH_Z19_ENABLED: False,
                MH_Z19_VALUE_OFFSET: 0,
                BME_280_ENABLED: False,
                BMP_280_ENABLED: False,
                DHT_22_PIN: DHT_22_DISABLED,
                MOTION_SENSOR_PIN: 23,
                WAVESHARE_DISP_BRIGHTNESS_PIN: 18,
                AUTO_UPDATER_ENABLED: True,
                UPDATER_USER_BETA_CHANNEL: False,
                LOG_SENSOR_DATA: True,
                SERVER_ENABLED: True,
                ALLOW_UNATTENDED_UPDATES: True,
                LAST_ALTITUDE_M_VALUE: 400.0,
                LAST_TEMP_C_OUTSIDE_VALUE: 23.5,
                REMOTE_MODE_URL: "",
                USER_SESSION_SECRET: bcrypt.gensalt(4).decode("utf-8"),
                USER_API_KEY: bcrypt.gensalt(4).decode("utf-8")[3:]
            },
            self._GUI_SECTION_NAME: {
                FONT_SCALING: 1.0,
                FONT_NAME: "Franzo",
                INTERIOR_BG: "background_s8.jpg",
                FORECAST_BG: "background_s9.jpg"
            },
            self._ENERGY_SECTION_NAME: {
                NIGHT_MODE_BEGIN: 22,
                NIGHT_MODE_END: 7,
                BRIGHTNESS: 90,
                MOTION_SENSOR_ENABLED: True,
                DAY_STANDBY_TIMEOUT: 600,
                NIGHT_STANDBY_TIMEOUT: 600
            },
            self._FORECAST_SECTION_NAME: {
                FORECAST_ENABLED: True,
                PREFER_ACCU_WEATHER: False,
                LOCATION: "None",
                OW_API_KEY: "",
                OW_CITY_IDS: {},
                AW_API_KEY: "",
                AW_CITY_IDS: {}}
        }

        self._read_ini()

    def get(self, name: str) -> Union[str, int, float, bool, Dict[str, str]]:
        """ Get a specific setting """
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
        return int(self.get(name)) # type: ignore

    def get_float(self, name: str) -> float:
        return float(self.get(name))  # type: ignore

    def get_bool(self, name: str) -> bool:
        return bool(self.get(name))

    def get_dict(self, name: str) -> Dict[str, str]:
        return self.get(name)  # type: ignore

    def set(self, setting_name: str, value: Union[str, int, float, bool]):
        """ Set the value of a specific setting. Does not write to file, if value is already set. """
        for section in self._values.keys():
            if setting_name in self._values[section]:
                if self._values[section][setting_name] == value:
                    return
                self._values[section][setting_name] = value
                break
        if self._auto_save:
            self.save()

    def save(self):
        """ Save all user modifiable options to file. """
        for section in self._values:
            for option in self._values[section]:
                self._write_setting(option, section)

        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _read_ini(self):
        """ Read settings ini with configparser. """
        update_needed = False
        try:
            self._parser.read(self._ini_file_path, encoding="UTF-8")
            for section in self._values.keys():
                for setting in self._values[section]:
                    update_needed |= self._read_setting(setting, section)
            self.read_city_ids()
        except Exception as e:
            self._logger.error(
                f"Settings: Can't read ini file: {str(e)}, trying to delete and create a new one...")
            os.remove(str(self._ini_file_path))  # let an exeception to the user, file can't be deleted

        # write file - to record defaults, if missing
        if not update_needed:
            return
        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def read_city_ids(self):
        # automatically get city ids from array elements
        forecast_section = self._get_section(self._FORECAST_SECTION_NAME)
        for key in forecast_section:
            if key.find(OW_CITY_IDS) == 0 or key.find(AW_CITY_IDS) == 0:
                val = forecast_section.get(key)
                val = val.split(",")
                if len(val) == 2:
                    if key.find(OW_CITY_IDS) == 0:
                        self.get(OW_CITY_IDS).update({val[0]: val[1]})
                    elif key.find(AW_CITY_IDS) == 0:
                        self.get(AW_CITY_IDS).update({val[0]: val[1]})

    def _get_section(self, section_name):
        """ Helper function to get a section from ini, or create it, if it does not exist."""
        if section_name not in self._parser:
            self._parser.add_section(section_name)
        return self._parser[section_name]

    def _read_setting(self, setting_name: str, section_name: str) -> bool:
        """ Helper function to get a setting, which uses the init value to determine the type. 
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
            value = float(section.get(setting_name))
        elif isinstance(default_value, int):
            value = int(section.get(setting_name))
        if value is None:
            self._logger.error(f"Settings: Setting {setting_name} is unknown", )
            return False
        # autosave must be disabled, otherwise we overwrite the other settings in the file
        auto_save = self._auto_save
        self._auto_save = False
        self.set(setting_name, value)
        self._auto_save = auto_save
        return False

    def _write_setting(self, option_name, section_name):
        """ Helper function to write an option. """
        value = self.get(option_name)
        if isinstance(value, dict):
            return  # dicts are read only currently

        section = self._get_section(section_name)
        if not option_name in section:
            self._logger.error("Option %s to write is unknown", option_name)
        section[option_name] = str(value)
