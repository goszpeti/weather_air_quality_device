"""
Test the Option UI.
"""

# import os
# import sys
# import threading
# import time
from waqd.ui.options import OptionMainUi
from waqd.ui.main_ui import WeatherMainUi
from PyQt5 import QtCore
from waqd.settings import Settings
from waqd.base.component_ctrl import ComponentController
from waqd import config

def testOptions(base_fixture, qtbot, target_mockup_fixture):
    """
    Test the option gui.
    """

    settings = Settings(base_fixture.testdata_path / "integration")
    comp_ctrl = ComponentController(settings)
    wmu = WeatherMainUi(comp_ctrl, settings)
    from pytestqt.plugin import _qapp_instance
    config.qt_app = _qapp_instance
    # OptionMainUi start a new root obj execution
    widget = OptionMainUi(wmu, comp_ctrl, settings)

    qtbot.addWidget(widget)

    widget.show()
    qtbot.waitForWindowShown(widget)

    # For debug:
   #  while True:
   #     _qapp_instance.processEvents()

    assert widget.isEnabled()
    qtbot.mouseClick(widget._ui.ok_button, QtCore.Qt.LeftButton)
    assert widget.isHidden()

    # TODO add r/w asserts
