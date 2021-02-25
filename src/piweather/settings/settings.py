import configparser
import logging
from pathlib import Path

from piweather.config import PROG_NAME
from piweather.settings import (
    CCS811_ENABLED, MH_Z19_ENABLED, AW_API_KEY, EVENTS_ENABLED,
    AW_CITY_IDS, BRIGHTNESS, DAY_STANDBY_TIMEOUT, DISP_TYPE_WAVESHARE,
    DISPLAY_TYPE, FONT_SCALING, FORECAST_ENABLED, LANG,
    LANG_GERMAN, LOCATION, MOTION_SENSOR_ENABLED, MOTION_SENSOR_PIN,
    NIGHT_MODE_BEGIN, NIGHT_MODE_END, NIGHT_STANDBY_TIMEOUT, OW_API_KEY,
    OW_CITY_IDS, PREFER_ACCU_WEATHER, SOUND_ENABLED, DHT_22_PIN, BMP_280_ENABLED,
    UPDATER_KEY, WAVESHARE_DISP_BRIGHTNESS_PIN, DHT_22_DISABLED)


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
            ini_folder = Path(ini_folder)
            self._ini_file_path = ini_folder / "config.ini"
        # create Settings ini file, if not available for first start
        if not self._ini_file_path.is_file():
            self._ini_file_path.open('a').close()
            self._logger.warning('Settings: Creating settings ini-file')
        else:
            self._logger.info('Settings: Using %s', self._ini_file_path)

        ### default setting values ###
        self._values = {
            # general
            LANG: LANG_GERMAN,
            SOUND_ENABLED: False,
            EVENTS_ENABLED: True,
            # general hw - read only
            DISPLAY_TYPE: DISP_TYPE_WAVESHARE,
            CCS811_ENABLED: True,
            MH_Z19_ENABLED: False,
            BMP_280_ENABLED: False,
            DHT_22_PIN: DHT_22_DISABLED,
            MOTION_SENSOR_PIN: 15,
            WAVESHARE_DISP_BRIGHTNESS_PIN: 18,
            UPDATER_KEY: "",
            # gui
            FONT_SCALING: 1.5,
            # energy saving
            NIGHT_MODE_BEGIN: 22,
            NIGHT_MODE_END: 7,
            BRIGHTNESS: 90,
            MOTION_SENSOR_ENABLED: True,
            DAY_STANDBY_TIMEOUT: 600,
            NIGHT_STANDBY_TIMEOUT: 600,
            # forecast
            FORECAST_ENABLED: True,
            PREFER_ACCU_WEATHER: False,
            LOCATION: "City1",
            OW_API_KEY: "",
            OW_CITY_IDS: {},
            AW_API_KEY: "",
            AW_CITY_IDS: {}
        }

        self._read_ini()

    def get(self, name: str):
        """ Get a specific setting """
        return self._values.get(name, None)  # TODO Name checking Error

    def set(self, name: str, value):
        """ Get a specific setting """
        self._values[name] = value  # TODO Name and type checking Error

    def _read_ini(self):
        """ Read settings ini with configparser. """
        self._parser.read(self._ini_file_path, encoding="UTF-8")

        general_section = self._get_section(self._GENERAL_SECTION_NAME)
        self._read_option(LANG, general_section)
        self._read_option(DISPLAY_TYPE, general_section)
        self._read_option(WAVESHARE_DISP_BRIGHTNESS_PIN, general_section)
        self._read_option(MOTION_SENSOR_PIN, general_section)
        self._read_option(DHT_22_PIN, general_section)
        self._read_option(BMP_280_ENABLED, general_section)
        self._read_option(CCS811_ENABLED, general_section)
        self._read_option(MH_Z19_ENABLED, general_section)
        self._read_option(UPDATER_KEY, general_section)
        self._read_option(SOUND_ENABLED, general_section)
        self._read_option(EVENTS_ENABLED, general_section)

        gui_section = self._get_section(self._GUI_SECTION_NAME)
        self._read_option(FONT_SCALING, gui_section)

        energy_section = self._get_section(self._ENERGY_SECTION_NAME)
        self._read_option(NIGHT_MODE_BEGIN, energy_section)
        self._read_option(NIGHT_MODE_END, energy_section)
        self._read_option(BRIGHTNESS, energy_section)
        self._read_option(MOTION_SENSOR_ENABLED, energy_section)
        self._read_option(DAY_STANDBY_TIMEOUT, energy_section)
        self._read_option(NIGHT_STANDBY_TIMEOUT, energy_section)

        forecast_section = self._get_section(self._FORECAST_SECTION_NAME)
        self._read_option(FORECAST_ENABLED, forecast_section)
        self._read_option(PREFER_ACCU_WEATHER, forecast_section)
        self._read_option(LOCATION, forecast_section)
        self._read_option(OW_API_KEY, forecast_section)
        self._read_option(AW_API_KEY, forecast_section)

        # automatically get city ids from array elements
        for key in forecast_section:
            if key.find(OW_CITY_IDS) == 0 or key.find(AW_CITY_IDS) == 0:
                val = forecast_section.get(key)
                val = val.split(",")
                if len(val) == 2:
                    if key.find(OW_CITY_IDS) == 0:
                        self._values[OW_CITY_IDS][val[0]] = val[1]
                    elif key.find(AW_CITY_IDS) == 0:
                        self._values[AW_CITY_IDS][val[0]] = val[1]

        # write file - to record defaults, if missing
        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _get_section(self, section_name):
        """ Helper function to get a section from ini, or create it, if it does not exist."""
        if section_name not in self._parser:
            self._parser.add_section(section_name)
        return self._parser[section_name]

    def _read_option(self, option_name, section):
        """ Helper function to get an option, which uses the init value to determine the type. """
        default_value = self._values[option_name]
        if not option_name in section:
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
        self._values[option_name] = value

    def save_all_options(self):
        """ Save all user modifiable options to file. """
        self._write_option(LANG, self._GENERAL_SECTION_NAME)
        self._write_option(SOUND_ENABLED, self._GENERAL_SECTION_NAME)
        self._write_option(EVENTS_ENABLED, self._GENERAL_SECTION_NAME)
        self._write_option(FONT_SCALING, self._GUI_SECTION_NAME)
        self._write_option(FORECAST_ENABLED, self._FORECAST_SECTION_NAME)
        self._write_option(LOCATION, self._FORECAST_SECTION_NAME)
        self._write_option(NIGHT_MODE_BEGIN, self._ENERGY_SECTION_NAME)
        self._write_option(NIGHT_MODE_END, self._ENERGY_SECTION_NAME)
        self._write_option(BRIGHTNESS, self._ENERGY_SECTION_NAME)
        self._write_option(MOTION_SENSOR_ENABLED, self._ENERGY_SECTION_NAME)
        self._write_option(DAY_STANDBY_TIMEOUT, self._ENERGY_SECTION_NAME)
        self._write_option(NIGHT_STANDBY_TIMEOUT, self._ENERGY_SECTION_NAME)

        with self._ini_file_path.open('w', encoding="utf8") as ini_file:
            self._parser.write(ini_file)

    def _write_option(self, option_name, section_name):
        """ Helper function to write an option. """
        section = self._get_section(section_name)
        if not option_name in section:
            self._logger.error("Option %s to write is unkonwn", option_name)
        section[option_name] = str(self._values[option_name])
