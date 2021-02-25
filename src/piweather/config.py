"""
Contains global constants and basic/ui variables.
Note: sensors where moved to component handler in base.
"""

from pathlib import Path

from PyQt5 import QtWidgets, QtCore

### Global constants ###
PROG_NAME = "W.A.Q.D"
GITHUB_REPO_NAME = "PIWEATHER"
FONT_NAME = "Weather Icons"

### Global variables ###
# 0: No debug, 1 = logging on, 2: remote debugging on
# 3: wait for remote debugger, multiprocessing off
DEBUG_LEVEL = 0

# paths to find folders
base_path: Path = Path(__file__).absolute().parent.parent
resource_path: Path = base_path / "resources"

# qt_application instance
qt_app: QtWidgets.QApplication = None

# translator instance for app translation
translator: QtCore.QTranslator = None
