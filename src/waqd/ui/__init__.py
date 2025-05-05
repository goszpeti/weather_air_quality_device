from pathlib import Path
from ..assets.assets import get_asset_file
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
        locale.setlocale(locale.LC_ALL, "C")

    local_date = time.strftime("%a, %x", date_time.timetuple())
    # remove year - twice once with following . and once for none
    local_date = local_date.replace(str(date_time.year) + ".", "")
    local_date = local_date.replace(str(date_time.year), "")
    return local_date


def format_unit_disp_value(
    quantity: Optional[Quantity], unit: bool = True, precision=int(1)
) -> str:
    """Format sensor value for display by appending the unit symbol (if unit is True) and float precision"""
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


def get_temperature_icon(temp_value: Optional[Quantity]) -> Path:
    """
    Return the path of the image resource for the appropriate temperature input.
    t < 0: empty
    t < 10: low
    t < 22: half
    t < 30 high
    t > 30: full
    """
    assets_subfolder = "weather_icons"
    # set dummy as default
    icon_path = get_asset_file(assets_subfolder, "thermometer_empty")
    # return dummy for invalid value
    if temp_value is None:
        return icon_path
    temp_deg_c = temp_value.m_as(app.unit_reg.degC)
    # set up ranges for the 5 icons
    if temp_deg_c <= 0:
        icon_path = get_asset_file(assets_subfolder, "thermometer_empty")
    elif temp_deg_c < 10:
        icon_path = get_asset_file(assets_subfolder, "thermometer_almost_empty")
    elif temp_deg_c < 22:
        icon_path = get_asset_file(assets_subfolder, "thermometer_half")
    elif temp_deg_c < 30:
        icon_path = get_asset_file(assets_subfolder, "thermometer_almost_full")
    else:
        icon_path = get_asset_file(assets_subfolder, "thermometer_full")
    return icon_path
