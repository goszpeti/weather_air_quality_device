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
Entry module of WAQD
Sets up cmd arguments, settings and starts the gui
"""


import platform
import time

import waqd
from waqd import INTRO_JINGLE
from waqd import __version__ as WAQD_VERSION
from waqd.assets import get_asset_file
from waqd.base.component_ctrl import ComponentController
from waqd.base.system import RuntimeSystem
from waqd.settings import (FONT_NAME,
                           FONT_SCALING,
                           Settings)


def qt_app_setup(settings: Settings) -> "QtWidgets.QApplication":
    """
    Set up all Qt application specific attributes, which can't be changed later on
    Returns qt_app object.
    """
    from PyQt5 import QtCore, QtGui, QtWidgets
    Qt = QtCore.Qt
    if platform.system() == "Windows":
        # Workaround for Windows, so that on the taskbar the
        # correct icon will be shown (and not the default python icon).
        from PyQt5.QtWinExtras import QtWin
        MY_APP_ID = 'ConanAppLauncher.' + WAQD_VERSION
        QtWin.setCurrentProcessExplicitAppUserModelID(MY_APP_ID)

    # apply Qt attributes (only at init possible)
    QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # set up global Qt Application instance
    qt_app = QtWidgets.QApplication([])
    # set icon
    icon_path = get_asset_file("gui_base", "icon")
    qt_app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    from waqd.ui.qt.common import set_ui_language

    # install translator
    set_ui_language(qt_app, settings)
    from waqd.ui.qt.theming import activate_theme
    activate_theme(settings.get_float(FONT_SCALING), settings.get_string(FONT_NAME))

    return qt_app


def qt_loading_sequence(comp_ctrl: ComponentController, settings: Settings):
    """
    Load modules with watchdog and display Splashscreen until loading is finished.
    """
    # init speech module - this takes a while, so the output will be effectively heard,
    # when the splash screen is already loading. It is a non-blocking call.

    # start init for all components
    from PyQt5 import QtCore, QtWidgets
    from waqd.ui.qt.main_window import WeatherMainUi
    from waqd.ui.qt.widgets.fader_widget import FaderWidget
    from waqd.ui.qt.widgets.splashscreen import SplashScreen
    # show splash screen
    splash_screen = SplashScreen()
    splash_screen.show()

    # wait for finishing loading - processEvents is needed for animations to work (loader)
    loading_minimum_time_s = 5
    start = time.time()
    if INTRO_JINGLE:
        comp_ctrl.components.sound.play(get_asset_file("sounds", "pera__introgui.wav"))
    while not comp_ctrl.all_ready:
        QtWidgets.QApplication.processEvents()

    # start gui init in separate qt thread
    app_main_ui = WeatherMainUi(comp_ctrl, settings)

    if RuntimeSystem().is_target_system:  # only remove titlebar on RPi
        app_main_ui.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
    thread = QtCore.QThread(app_main_ui)
    thread.started.connect(app_main_ui.init_gui)
    thread.start()
    while (not app_main_ui.ready) \
        or (time.time() < start + loading_minimum_time_s) \
            and waqd.DEBUG_LEVEL <= 3:
        QtWidgets.QApplication.processEvents()

    # splash screen can be disabled - with fader
    app_main_ui.show()
    fade_length = 1  # second
    fader_widget = FaderWidget(  # pylint: disable=unused-variable
        splash_screen, app_main_ui, length=fade_length*1000)
    splash_screen.finish(app_main_ui)
    return app_main_ui

