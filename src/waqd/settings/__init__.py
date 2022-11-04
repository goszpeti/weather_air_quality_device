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


# use constants in class, so they don't need to be separately accessed
# use constants for string options
LANG_GERMAN = "Deutsch"
LANG_ENGLISH = "English"
LANG_HUNGARIAN = "Magyar"
DISP_TYPE_RPI = "RPI_TD" # original 7" rpi touch display
DISP_TYPE_WAVESHARE_5_LCD = "Waveshare_LCD" # Waveshare 5" touch display
DISP_TYPE_WAVESHARE_EPAPER_2_9 = "Waveshare_Epaper_2_9"
DHT_22_DISABLED = 0


# constants for option names - value (ini name) should be very similar to internal string
# general
LANG = "lang"
SOUND_ENABLED = "sound_enabled"
EVENTS_ENABLED = "events_enabled"
SERVER_ENABLED = "server_enabled"
# general hw
DISPLAY_TYPE = "display_type"
DHT_22_PIN = "dht_22_pin"  # on if not DHT_22_DISABLED (0)
BMP_280_ENABLED = "bmp_280_enabled"
BME_280_ENABLED = "bme_280_enabled"
MOTION_SENSOR_PIN = "motion_sensor_pin"
WAVESHARE_DISP_BRIGHTNESS_PIN = "waveshare_disp_brightness_pin"
CCS811_ENABLED = "ccs811_enabled"
MH_Z19_ENABLED = "mh_z19_enabled"
MH_Z19_VALUE_OFFSET = "mh_z19_value_offset"
LOG_SENSOR_DATA = "log_sensor_data"
USER_SESSION_SECRET = "user_session_secret"
USER_API_KEY = "user_api_key"

AUTO_UPDATER_ENABLED = "auto_updater_enabled"
UPDATER_USER_BETA_CHANNEL = "updater_use_beta_channel"
ALLOW_UNATTENDED_UPDATES = "unattended_updates" # TODO does nothing

LAST_ALTITUDE_M_VALUE = "last_alitude_value"
LAST_TEMP_C_OUTSIDE_VALUE  = "last_temp_outside_value"
REMOTE_MODE_URL = "remote_mode_url"
# gui
FONT_SCALING = "font_scaling"
FONT_NAME = "font_name"
FORECAST_BG = "forecast_background"
INTERIOR_BG = "interior_background"

# energy saving
NIGHT_MODE_BEGIN = "night_mode_begin"
NIGHT_MODE_END = "night_mode_end"
BRIGHTNESS = "brightness"
MOTION_SENSOR_ENABLED = "motion_sensor_enabled"  # redundant with pin number, this is for user settings
DAY_STANDBY_TIMEOUT = "day_standby_timeout"
NIGHT_STANDBY_TIMEOUT = "night_standby_timeout"
# forecast
FORECAST_ENABLED = "forecast_enabled"
PREFER_ACCU_WEATHER = "prefer_accu_weather"
LOCATION = "location"
OW_API_KEY = "open_weather_api_key"
OW_CITY_IDS = "ow_city_id"
AW_API_KEY = "accu_weather_api_key"
AW_CITY_IDS = "aw_city_id"

# import at the end, to avoid circular imports
from waqd.settings.settings import Settings
