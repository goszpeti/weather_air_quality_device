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
from pathlib import Path

from waqd.config import PROG_NAME
from waqd.settings import (AUTO_UPDATER_ENABLED,
    CCS811_ENABLED, FORECAST_BG, INTERIOR_BG, MH_Z19_ENABLED, AW_API_KEY, EVENTS_ENABLED, FONT_NAME,
    AW_CITY_IDS, BRIGHTNESS, DAY_STANDBY_TIMEOUT, DISP_TYPE_RPI,
    DISPLAY_TYPE, FONT_SCALING, FORECAST_ENABLED, LANG, UPDATER_USER_BETA_CHANNEL,
    LANG_GERMAN, LOCATION, MOTION_SENSOR_ENABLED, MOTION_SENSOR_PIN,
    NIGHT_MODE_BEGIN, NIGHT_MODE_END, NIGHT_STANDBY_TIMEOUT, OW_API_KEY,
    OW_CITY_IDS, PREFER_ACCU_WEATHER, SOUND_ENABLED, DHT_22_PIN, BME_280_ENABLED, BMP_280_ENABLED,
    UPDATER_KEY, WAVESHARE_DISP_BRIGHTNESS_PIN, DHT_22_DISABLED, LOG_SENSOR_DATA)


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

    def __init__(self, ini_folder=None):
        """
        Read config.ini file to load settings.
        Verify config.ini existence, if folder is passed.
        """
        self._logger = logging.getLogger(PROG_NAME)
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

        ### default setting values ###
        self._values = {
            self._GENERAL_SECTION_NAME: {
                LANG: LANG_GERMAN,
                SOUND_ENABLED: False,
                EVENTS_ENABLED: True,
                DISPLAY_TYPE: DISP_TYPE_RPI,
                CCS811_ENABLED: False,
                MH_Z19_ENABLED: False,
                BME_280_ENABLED: False,
                BMP_280_ENABLED: False,
                DHT_22_PIN: DHT_22_DISABLED,
                MOTION_SENSOR_PIN: 15,
                WAVESHARE_DISP_BRIGHTNESS_PIN: 18,
                UPDATER_KEY: "",
                AUTO_UPDATER_ENABLED: True,
                UPDATER_USER_BETA_CHANNEL: False,
                LOG_SENSOR_DATA: True
            },
            self._GUI_SECTION_NAME: {
                FONT_SCALING: 1.3,
                FONT_NAME : "Franzo",
                INTERIOR_BG: "background_s8.jpg",
                FORECAST_BG: "background_s9.jpg"
            },
            self._ENERGY_SECTION_NAME: {
                NIGHT_MODE_BEGIN: 22,
                NIGHT_MODE_END: 7,
                BRIGHTNESS: 90,
                MOTION_SENSOR_ENABLED: True,
                DAY_STANDBY_TIMEOUT: 600,
                NIGHT_STANDBY_TIMEOUT: 600, },
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

    def get(self, name: str):
        """ Get a specific setting """
        value = None
        for section in self._values:
            if name in self._values[section]:
                value = self._values[section].get(name, None)
                break
        return value

    def set(self, name: str, value):
        """ Get a specific setting """
        for section in self._values:
            if name in self._values[section]:
                self._values[section][name] = value
                return

    def _read_ini(self):
        """ Read settings ini with configparser. """
        self._parser.read(self._ini_file_path, encoding="UTF-8")
        for section in self._values:
            for option in self._values[section]:
                self._read_option(option, section)

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
        # write file - to record defaults, if missing
        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _get_section(self, section_name):
        """ Helper function to get a section from ini, or create it, if it does not exist."""
        if section_name not in self._parser:
            self._parser.add_section(section_name)
        return self._parser[section_name]

    def _read_option(self, option_name, section_name):
        """ Helper function to get an option, which uses the init value to determine the type. """
        section = self._get_section(section_name)
        default_value = self.get(option_name)
        if isinstance(default_value, dict): # no dicts upported directly
            return

        if not option_name in section: # write out
            section[option_name] = str(default_value)
            return

        value = None
        if isinstance(default_value, bool):
            value = section.getboolean(option_name)
        elif isinstance(default_value, str):
            value = section.get(option_name)
        elif isinstance(default_value, float):
            value = float(section.get(option_name))
        elif isinstance(default_value, int):
            value = int(section.get(option_name))
        if value is None:
            raise Exception("Unsupported type " +
                            str(type(default_value)) + " of setting " + option_name)
        self.set(option_name, value)

    def save_all_options(self):
        """ Save all user modifiable options to file. """
        for section in self._values:
            for option in self._values[section]:
                self._write_option(option, section)

        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _write_option(self, option_name, section_name):
        """ Helper function to write an option. """
        value = self.get(option_name)
        if isinstance(value, dict):
            return  # dicts are read only currently

        section = self._get_section(section_name)
        if not option_name in section:
            self._logger.error("Option %s to write is unknown", option_name)
        section[option_name] = str(value)
