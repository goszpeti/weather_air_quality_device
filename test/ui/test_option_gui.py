"""
Test the Option UI.
"""

import time
from waqd.ui.qt.options import OptionMainUi
from waqd.ui.qt.main_ui import WeatherMainUi
from PyQt5 import QtCore
from waqd.settings import Settings
from waqd.base.component_ctrl import ComponentController
import waqd

from test.conftest import mock_run_on_target

def testOptions(base_fixture, qtbot, mocker):  # target_mockup_fixture
    """
    Test the option gui.
    """
    mock_run_on_target(mocker)
    settings = Settings(base_fixture.testdata_path / "integration")
    comp_ctrl = ComponentController(settings)
    wmu = WeatherMainUi(comp_ctrl, settings)
    from pytestqt.plugin import _qapp_instance
    # OptionMainUi start a new root obj execution
    widget = OptionMainUi(wmu, comp_ctrl, settings)

    qtbot.addWidget(widget)

    widget.show()
    qtbot.waitExposed(widget)

    # For debug:
    while True:
       _qapp_instance.processEvents()

    assert widget.isEnabled()
    qtbot.mouseClick(widget._ui.ok_button, QtCore.Qt.LeftButton)
    assert widget.isHidden()
    

    # TODO add r/w asserts

    # unload the now started main ui
    wmu.unload_gui()
    comp_ctrl.unload_all()
    while not comp_ctrl.all_unloaded:
        time.sleep(.1)
    time.sleep(3)
    assert comp_ctrl.all_unloaded
