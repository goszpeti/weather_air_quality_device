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

"""
Contains global constants and basic/ui variables.
Should not contain any 3rd party imports!
"""

from pathlib import Path

__version__ = "1.6.0b5"

### Global constants ###
PROG_NAME = "W.A.Q.D"
GITHUB_REPO_NAME = "goszpeti/WeatherAirQualityDevice"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

### Global variables ###
# 0: No debug, 1 = logging on, 2: remote debugging on
# 3: wait for remote debugger, 4: quick-load
DEBUG_LEVEL = 0

# paths to find folders
base_path = Path(__file__).absolute().parent
assets_path = base_path / "assets"
user_config_dir = Path().home() / ".waqd"
