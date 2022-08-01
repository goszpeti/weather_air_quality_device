from pathlib import Path

import waqd.app as app


from jinja2 import Template
from PyQt5.QtWidgets import QApplication
from waqd.ui import common


def configure_theme(qss_template_path: Path, font_size_pt: int, font_family:str) -> str:
    """ Configure the given qss file with the set options and return it as a string """

    qss_template = None
    with open(qss_template_path, "r") as fd:
        qss_template = Template(fd.read())
    qss_content = qss_template.render(MAIN_FONT_SIZE=font_size_pt, FONT_FAMILY=font_family)
    return qss_content


def activate_theme(scaling: float, font_family: str):
    """ Apply the theme from the current settings and apply all related view options """
    common.apply_font(font_family)

    style_file = "light_style.qss.in"
    base_font_size = 12
    scaled_font_size = int(base_font_size * scaling)
    style_sheet = configure_theme(app.base_path / "ui" / style_file, scaled_font_size, font_family)

    qapp = QApplication.instance()
    if not qapp:
        return
    qapp.setStyleSheet(style_sheet)
