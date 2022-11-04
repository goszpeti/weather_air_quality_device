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
""" This module holds all gui relevant classes. """
import os
from pathlib import Path

import waqd
from waqd.base.logger import Logger

# compile uic files at dev time, if needed
if waqd.DEBUG_LEVEL > 0:
    current_dir = Path(__file__).parent
    for ui_file in current_dir.glob("**/*.ui"):
        py_ui_file = Path("NULL")
        try:
            py_ui_file = ui_file.parent / (ui_file.stem + "_ui.py")
            if py_ui_file.exists() and py_ui_file.stat().st_mtime > ui_file.stat().st_mtime:
                continue
            Logger().debug("Converting " + str(py_ui_file))
            os.system(f"pyuic5 -o {str(py_ui_file)} {str(ui_file)}")
        except Exception as e:
            Logger().warning(f"Can't convert {str(py_ui_file)}: {str(e)}")
# only import after uis where compiled
from . import common, main_ui, options, qt, widgets
