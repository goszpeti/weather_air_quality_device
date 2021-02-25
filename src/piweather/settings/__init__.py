
# use constants in class, so they don't need to be separately accessed
# use constants for string options
LANG_GERMAN = "Deutsch"
LANG_ENGLISH = "English"
LANG_HUNGARIAN = "Magyar" 
DISP_TYPE_RPI = "RPI_TD"
DISP_TYPE_WAVESHARE = "Waveshare"
DHT_22_DISABLED = 0


# constants for option names
# general
LANG = "lang"
SOUND_ENABLED = "sound_enabled"
EVENTS_ENABLED = "events_enabled"
# general hw - read only
DISPLAY_TYPE = "display_type"
DHT_22_PIN = "dht_22_pin"  # on if not DHT_22_DISABLED (0)
BMP_280_ENABLED = "bmp_280_enabled"
MOTION_SENSOR_PIN = "motion_sensor_pin"
WAVESHARE_DISP_BRIGHTNESS_PIN = "waveshare_disp_brightness_pin"
CCS811_ENABLED = "ccs811_enabled"
MH_Z19_ENABLED = "mh_z19_enabled"

# airquality needs sca-scl
UPDATER_KEY = "updater_key"
# gui
FONT_SCALING = "font_scaling"
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
from piweather.settings.settings import Settings
