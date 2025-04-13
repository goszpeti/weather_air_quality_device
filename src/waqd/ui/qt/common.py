
""" Contains helper methods usually to display some text or image with formatting."""

import xml.dom.minidom as dom
from pathlib import Path
from typing import Optional, Union
from pint import Quantity, Unit

from PyQt5 import QtCore, QtSvg, QtGui, QtWidgets
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
import waqd
import waqd.app as app
from waqd.assets import get_asset_file
from waqd.settings import LANG, LANG_ENGLISH, LANG_GERMAN, LANG_HUNGARIAN, Settings
from waqd.base.file_logger import Logger

# define Qt so it can be used like the namespace in C++
Qt = QtCore.Qt


def get_font(font_name) -> QFont:
    # set up font
    font_file = get_asset_file("font", "franzo")
    font_id = QFontDatabase.addApplicationFont(str(font_file))
    qapp = QApplication.instance()
    if qapp is None:
        return QFont()
    font = qapp.font()  # type: ignore
    if font_id != -1:
        font_db = QFontDatabase()
        font_styles = font_db.styles(font_name)
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            font = font_db.font(font_families[0], font_styles[0], 13)
        else:
            Logger().warning("Can't apply selected font file.")
    return font


def apply_font(font_name: str):
    font = get_font(font_name)
    qapp = QApplication.instance()
    if qapp is None:
        return
    qapp.setFont(font)  # type: ignore


def set_ui_language(qt_app: QApplication, settings: Settings):
    """ Set the ui language. Retranslate must be called afterwards."""
    if app.translator:
        qt_app.removeTranslator(app.translator)
    if app.base_translator:
        qt_app.removeTranslator(app.base_translator)
    if settings.get(LANG) == LANG_ENGLISH:  # default case, ui is written in english
        return

    if not app.translator:
        app.translator = QtCore.QTranslator(qt_app)
    if not app.base_translator:
        app.base_translator = QtCore.QTranslator(qt_app)

    tr_file = Path("NULL")
    tr_base_file = None
    if settings.get(LANG) == LANG_GERMAN:
        tr_file = waqd.base_path / "ui/qt/qt/german.qm"
        tr_base_file = Path(QtCore.__file__).parent / "Qt5/translations/qtbase_de.qm"
    if settings.get(LANG) == LANG_HUNGARIAN:
        tr_file = waqd.base_path / "ui/qt/qt/hungarian.qm"
        tr_base_file = Path(QtCore.__file__).parent / "Qt5/translations/qtbase_hu.qm"
    if not tr_file.exists():
        Logger().error("Cannot find %s translation file.", str(tr_file))

    app.translator.load(str(tr_file))
    qt_app.installTranslator(app.translator)
    if tr_base_file:
        app.base_translator.load(str(tr_base_file))
        qt_app.installTranslator(app.base_translator)


def draw_svg(pyqt_obj: QLabel, svg_path: Path, color="white", shadow=False, scale: float = 1.0):
    """
    Sets an svg in the desired color for a QtWidget.
    :param color: the disired color as a string in html compatible name
    :param shadow: draws a drop shadow
    :param scale: multiplicator for scaling the image
    """
    if not svg_path or not svg_path.exists():
        Logger().error("Cannot draw invalid SVG file: %s", repr(svg_path))
        return

    # read svg as xml and get the drawing
    with open(svg_path) as svg:
        svg_content = "".join(svg.readlines())
        svg_content = svg_content.replace("\t", "")
    svg_dom = dom.parseString("".join(svg_content))
    svg_drawing = svg_dom.getElementsByTagName("path")

    # set color in the dom element
    svg_drawing[0].setAttribute("fill", color)

    # create temporary svg and read into pyqt svg graphics object
    svg_name = ""
    with open(svg_path.parent / Path(svg_path.stem + "_white" + svg_path.suffix), "w+") as new_svg:
        new_svg.write(svg_dom.toxml())
        new_svg.close()
        svg_name = new_svg.name

    svg_graphics = QtSvg.QGraphicsSvgItem(svg_name)

    # the gui needs a picture/painter to render the svg into
    pic = QtGui.QPicture()
    painter = QtGui.QPainter(pic)
    painter.scale(scale, scale)
    # now render and set picture
    svg_graphics.renderer().render(painter)
    pyqt_obj.setPicture(pic)

    # apply shadow, if needed
    if shadow:
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        pyqt_obj.setGraphicsEffect(shadow)

    painter.end()


def scale_gui_elements(qt_root_obj: QWidget, font_scaling: float,
                       previous_scaling: float = 1, extra_scaling=1):
    """
    Applies font resize for all QLabel, QPushButton and QTabWidget children of the qt_root_obj.
    :param font_scaling: new multiplicator
    :param previous_scaling: old multiplicator
    :param extra_scaling: for platform specific font size
    """
    if font_scaling > 1:  # normalize to 0-1
        font_scaling = 1
    # scale all fonts by font_scaling setting
    for qt_list in (
            qt_root_obj.findChildren(QtWidgets.QLabel),
            qt_root_obj.findChildren(QtWidgets.QPushButton),
            qt_root_obj.findChildren(QtWidgets.QComboBox),
            qt_root_obj.findChildren(QtWidgets.QTabWidget)):
        for qt_obj in qt_list:
            font = qt_obj.font()
            font.setPointSize(round(qt_obj.fontInfo().pointSize() * font_scaling * extra_scaling /
                                    previous_scaling))
            qt_obj.setFont(font)


def apply_shadow_to_labels(qt_root_obj):
    for label in qt_root_obj.findChildren(QtWidgets.QLabel):
        effect = QtWidgets.QGraphicsDropShadowEffect()
        effect.setBlurRadius(3)
        effect.setOffset(2, 2)
        label.setGraphicsEffect(effect)


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
        icon_path = get_asset_file(
            assets_subfolder, "thermometer_almost_empty")
    elif temp_deg_c < 22:
        icon_path = get_asset_file(assets_subfolder, "thermometer_half")
    elif temp_deg_c < 30:
        icon_path = get_asset_file(
            assets_subfolder, "thermometer_almost_full")
    else:
        icon_path = get_asset_file(assets_subfolder, "thermometer_full")
    return icon_path

#### Formatting ####


def format_int_meas_text(html_text: str, value: Optional[Union[int, float, Quantity]], color="white", tag_id=0, unit: Optional[Unit] = None):
    """
    Returns a given html string by switching out the value with the given number.
    :param html_text: the html text containing the value. Can only contain one value.
    :param value: the value to be set
    """
    # converting of values to formatted display data
    if value is None:
        temp_val = format_text(html_text, "N/A", "string", color=color, tag_id=tag_id)
    else:
        if unit and isinstance(value, Quantity):
            temp_val = format_text(html_text, int(value.m_as(unit)), "int", color=color, tag_id=tag_id)
        else:
            temp_val = format_text(html_text, int(value), "int", color=color, tag_id=tag_id)
    return temp_val


def format_float_temp_text(html_text: str, value: Optional[Quantity], color="white"):
    """
    Returns a given html string by switching out the value with the given number.
    :param html_text: the html text containing the value. Can only contain one value.
    :param value: the value to be set
    """
    # converting of values to formatted display data
    if value is None:
        temp_val = format_text(html_text, "N/A", "string", color=color)
    else:
        temp_val = format_text(html_text, float(value.m_as(app.unit_reg.degC)), "float", color=color)
    return temp_val


def format_temp_text_minmax(html_text, min_val, max_val, color="white"):
    """
    Returns a given html string by switching out the min and max value with the given number.
    :param html_text: the html text containing the value. Can only contain two values: min and then max.
    :param min_val, max_val: the min and max value to be set
    """
    # converting of values to formatted display data
    if min_val is None or max_val is None:
        html_text = format_text(html_text, "N/A", "string", tag_id=0, color=color)
    else:
        # try-except, to avoid crashes, when values cannot be rounded (e.g. value is infinity)
        try:
            min_val = round(min_val)
            max_val = round(max_val)
            html_text = format_text(html_text, min_val, "int", tag_id=0, color=color)
            html_text = format_text(html_text, max_val, "int", tag_id=3, color=color)
        except Exception as e:
            Logger().error(f"Cannot format text: {str(e)}.")
    return html_text


def format_text(html_text: str, value: Union[str, int, float, None],
                disp_type: str, tag_id=0, color="white") -> str:
    """
    Generic hmtl text formatting method.
    :param html_text: the html text containing the value.
    :param value: the value to be set
    :param disp_type: format for the html for "float", "int" or "string"
    :param tag_id: tag containing the value
    :param color: apply this html color
    """
    if value is None:
        value = 0.0
    if not html_text:
        return ""
    html_dom = dom.parseString(html_text)
    # set color
    tags = html_dom.getElementsByTagName("span")
    if tags:
        tags[0].setAttribute("style", "color:" + color)

    # type scpecific handling
    if disp_type == "float" and isinstance(value, float):
        text = "{:0.1f}".format(value)
        split_text = text.split(".")
        tags = html_dom.getElementsByTagName("span")
        if len(tags) >= 2:
            tags[tag_id].firstChild.data = str(split_text[tag_id] + ".")
            tags[tag_id+1].firstChild.data = str(int(split_text[tag_id+1]))
            return html_dom.toxml()

    if disp_type == "int" and isinstance(value, int):
        text = str(value)
        if tags:
            tags[tag_id].firstChild.data = text
            return html_dom.toxml()

    if disp_type == "string" and isinstance(value, str):
        if tags:
            for tag in tags:
                if tag.firstChild:
                    tag.firstChild.data = ""
            tags[tag_id].firstChild.data = value
            return html_dom.toxml()
    return ""
