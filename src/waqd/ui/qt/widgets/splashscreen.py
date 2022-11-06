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
from PyQt5 import QtCore, QtGui, QtWidgets
try:
    from sip import voidptr  # Raspberry
except ImportError:
    from PyQt5.sip import voidptr  # Windows x64

from pyqtspinner.spinner import WaitingSpinner

import waqd
from waqd import __version__ as WAQD_VERSION
from waqd.assets import get_asset_file

# define Qt so it can be used like the namespace in C++
Qt = QtCore.Qt


class SplashScreen(QtWidgets.QSplashScreen):
    """
    Generic splashscreen. Must always be spawned in a new thread, while the original thread
    executes qt_app.processEvents() in a while loop, until it should be stopped.
    """

    def __init__(self, background=True):
        """
        background: set the image as the background.
        The layout changes if background ist set.
        Without: the spinner plays in the middle. A screenshot is taken when the splashcreen
        initializes and set as background, so changing elements in the gui are not seen by the user.
        With: background image is scaled and spinner plays in the bottom middle.
        """
        self._is_background_set = background
        self._label = None
        self._spinner = None

        if background:
            pixmap = QtGui.QPixmap(str(get_asset_file("gui_base", "loading")))
            pixmap = pixmap.scaled(800, 480, transformMode=Qt.SmoothTransformation)
        else:
            screen = QtWidgets.QApplication.instance().primaryScreen()
            pixmap = screen.grabWindow(voidptr(0))

        QtWidgets.QSplashScreen.__init__(self, pixmap)
        if waqd.DEBUG_LEVEL > 0: # unlock gui when debugging
            self.setWindowFlags(Qt.FramelessWindowHint)

    def mousePressEvent(self, event):  # pylint: disable=unused-argument, invalid-name, no-self-use
        """ Do nothing on mouse click. Otherwise it disappears. """
        return

    def showEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Start movie, when it is shown. """

        # show version label
        if self._is_background_set:
            self._label = QtWidgets.QLabel(self)
            self._label.setText(WAQD_VERSION + "   ")
            self._label.setAlignment(Qt.AlignmentFlag(Qt.AlignBottom | Qt.AlignRight))
            self._label.setGeometry(0, 0, 800, 480)
            self._label.show()
        self._spinner = WaitingSpinner(self, centerOnParent=False, radius=30, roundness=60,
                                      line_length=20, line_width=6, speed=0.5, color=(15, 67, 116))
        if self._is_background_set:
            self._spinner.setGeometry(int(self.width()/2 - self._spinner.width()/2),
                                     int(self.height() - self._spinner.height() - 20),
                                     self._spinner.width(),
                                     self._spinner.height())
        else:
            self._spinner.setColor(Qt.white)
            self._spinner.setInnerRadius(40)
            self._spinner.setLineLength(40)
            self._spinner.setLineWidth(8)
            self._spinner.setTrailFadePercentage(90)
            self._spinner.setGeometry(int(self.width()/2 - self._spinner.width()/2),
                                      int(self.height()/2 - self._spinner.height()/2),
                                     self._spinner.width(),
                                     self._spinner.height())
        self._spinner.start()

    def hideEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Stop movie, when it is hidden. """
        if self._spinner:
            self._spinner.stop()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.deleteLater()
        return super().closeEvent(a0)
