"""

"""

# import os
# import sys
# import threading
# import time
from piweather.ui.options import OptionMainUi
from piweather.ui.main_ui import WeatherMainUi
from PyQt5 import QtCore, QtWidgets
from piweather.settings import Settings
from piweather.base.component_ctrl import ComponentController
from piweather import config
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)


def testOptions(base_fixture, qtbot):
    """
    Test the option gui.
    """

    settings = Settings(base_fixture.testdata_path / "integration")
    comp_ctrl = ComponentController(settings)
    wmu = WeatherMainUi(comp_ctrl, settings)
    #root_obj = QtWidgets.QWidget()
    # qtbot.addWidget(root_obj)
    from pytestqt.plugin import _qapp_instance
    config.qt_app = _qapp_instance
    # OptionMainUi start a new root obj execution
    widget = OptionMainUi(wmu, comp_ctrl, settings)

    qtbot.addWidget(widget)

    widget._qt_root_obj.show()
    qtbot.waitForWindowShown(widget._qt_root_obj)

    # assert widget._qt_root_obj.isEnabled()
    # qtbot.mouseClick(widget._button_box.buttons()[0], Qt.LeftButton)
    #assert widget.isHidden()
