

"""
Contains global constants and basic/ui variables.
Should not contain any 3rd party imports!
"""

from enum import Enum
from pathlib import Path
import datetime
__version__ = "2.1.0"

### Global constants ###
PROG_NAME = "WAQD"
GITHUB_REPO_NAME = "goszpeti/WeatherAirQualityDevice"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

### Feature Flags ###
SELECTEBLE_LOGGER_INTERVAL_VIEW = False


class WeatherDataProviders(Enum):  # promote to settings, after stable
    OpenWeatherMap = 0
    AccuWeather = 1  # Currently not implemented
    OpenMeteo = 2


WEATHER_DATA_PROVIDER = 2

### Global variables ###
# 0: No debug, 1 = logging on, 2: remote debugging on
# 3: wait for remote debugger, 4: quick-load
DEBUG_LEVEL = 0
HEADLESS_MODE = False
MIGRATE_SENSOR_LOGS = False
LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
INTRO_JINGLE = True

# paths to find folders
base_path = Path(__file__).absolute().parent
assets_path = base_path / "assets"
user_config_dir = Path().home() / ".waqd"
