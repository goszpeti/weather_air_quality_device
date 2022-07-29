from pathlib import Path

import waqd.app as app


from jinja2 import Template
from PyQt5.QtWidgets import QApplication


def configure_theme(qss_template_path: Path, font_size_pt: int) -> str:
    """ Configure the given qss file with the set options and return it as a string """

    qss_template = None
    with open(qss_template_path, "r") as fd:
        qss_template = Template(fd.read())
    qss_content = qss_template.render(MAIN_FONT_SIZE=font_size_pt)
    return qss_content


def activate_theme(scaling: float):
    """ Apply the theme from the current settings and apply all related view options """


    style_file = "light_style.qss.in"
    base_font_size = 12
    scaled_font_size = int(base_font_size * scaling)
    style_sheet = configure_theme(app.base_path / "ui" / style_file, scaled_font_size)

    qapp = QApplication.instance()
    if not qapp:
        return
    qapp.setStyleSheet(style_sheet)
