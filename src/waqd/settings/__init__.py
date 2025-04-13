


# use constants in class, so they don't need to be separately accessed
# use constants for string options
LANG_GERMAN = "Deutsch"
LANG_ENGLISH = "English"
LANG_HUNGARIAN = "Magyar"
DISP_TYPE_RPI = "RPI_TD" # original 7" rpi touch display
DISP_TYPE_WAVESHARE_5_LCD = "Waveshare_LCD" # Waveshare 5" touch display
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
USER_DEFAULT_PW = "user_default_pw"

AUTO_UPDATER_ENABLED = "auto_updater_enabled"
UPDATER_USER_BETA_CHANNEL = "updater_use_beta_channel"

LAST_TEMP_C_OUTSIDE  = "last_temp_outside_value" # TODO write
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
LOCATION = "location" # only for display and search purposes
LOCATION_LONGITUDE = "location_long"
LOCATION_LATITUDE = "location_lat"
LOCATION_ALTITUDE_M = "last_altitude_value"

OW_API_KEY = "open_weather_api_key"
OW_CITY_IDS = "ow_city_id" # deprecate with generic geo conding
AW_API_KEY = "accu_weather_api_key"
AW_CITY_IDS = "aw_city_id"  # deprecate with generic geo conding

# import at the end, to avoid circular imports
from waqd.settings.settings import Settings
