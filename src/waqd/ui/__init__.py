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

from waqd.base.file_logger import Logger
import locale
import platform
import time
import datetime
from typing import Optional
from pint import Quantity
from waqd.settings import LANG, LANG_ENGLISH, LANG_GERMAN, LANG_HUNGARIAN, Settings
from waqd.app import unit_reg


def get_localized_date(date_time: datetime.datetime, settings: Settings) -> str:
    """
    Returns a formatted date of a day conforming to the actual locale.
    Contains weekday name, month and day.
    """
    # switch locale to selected language - needs reboot on linux
    if settings.get(LANG) != LANG_ENGLISH:
        locale_name = ""
        try:
            if platform.system() == "Windows":
                if settings.get(LANG) == LANG_GERMAN:
                    locale_name = "de_DE"
                elif settings.get(LANG) == LANG_HUNGARIAN:
                    locale_name = "hu-HU"
            elif platform.system() == "Linux":
                if settings.get(LANG) == LANG_GERMAN:
                    locale_name = "de_DE.UTF8"
                elif settings.get(LANG) == LANG_HUNGARIAN:
                    locale_name = "hu_HU.UTF8"
            locale.setlocale(locale.LC_ALL, locale_name)
        except Exception as error:
            Logger().error("Cannot set language to %s: %s", settings.get(LANG), str(error))
            # "sudo apt-get install language-pack-id" is needed...
            # or sudo locale-gen
    else:
        locale.setlocale(locale.LC_ALL, 'C')

    local_date = time.strftime("%a, %x", date_time.timetuple())
    # remove year - twice once with following . and once for none
    local_date = local_date.replace(str(date_time.year) + ".", "")
    local_date = local_date.replace(str(date_time.year), "")
    return local_date


def format_unit_disp_value(quantity: Optional[Quantity], unit="True", precision=1) -> str:
    """ Format sensor value for display by appending the unit symbol (if unit is True) and float precision """
    disp_value = "N/A"
    if quantity is not None:
        if isinstance(quantity, Quantity):
            disp_value = f"{float(quantity.m):.{precision}f}"
            if unit:
                disp_value += " " + unit_reg.get_symbol(str(quantity.u))
        else:
            disp_value = f"{float(quantity):.{precision}f}"
            if unit:
                disp_value += " " + unit
    return disp_value
