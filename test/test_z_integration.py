"""
This test starts the application.
It is called z_integration, so that it launches last.
"""

import os
import sys
import threading
import time
from piweather.ui.main_ui import WeatherMainUi
from PyQt5 import QtCore, QtWidgets

from subprocess import Popen


def testDebugDisabledForRelease(base_fixture):
    from piweather import config
    assert config.DEBUG_LEVEL == 0  # debug level should be 0 for release


def testSmoke(base_fixture, qtbot):
    sys.argv = []

    # conan_app_launcher
    proc = Popen(["python3", str(base_fixture.base_path / "src" / "main.py")])
    time.sleep(20)
    assert proc.poll() is None
    proc.terminate()
    time.sleep(3)
    assert proc.poll() != 0  # terminate exits os dependently, but never with success (0)
