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
from PyQt5 import QtGui, QtWidgets

from waqd.ui.widgets.fader_widget import FaderWidget


class FadingImage(QtWidgets.QStackedWidget):
    """ Fade between two images. Use a QStackedWidget. Uses FaderWidget. """

    def __init__(self, parent=None):
        QtWidgets.QStackedWidget.__init__(self, parent)
        self._pixmap_path = None
        self._active_widget = 0
        self._fade_disabled = False
        self._fader_widget = None

    @property
    def text(self):
        """ Return the text from the child label """
        label = self.widget(self.currentIndex()).findChild(QtWidgets.QLabel)
        if label:
            return label.text()
        return ""

    def set_text(self, text):
        """ Set text to the visible child label """
        if self.text != text:
            # app crashes if nonvisible elements are animated
            self._fade_disabled = False
            if not self.isVisible():
                self._fade_disabled = True

            if self.currentIndex() == 0:
                label = self.widget(1).findChild(QtWidgets.QLabel)
                if label:
                    label.setText(text)
                self.setCurrentIndex(1)
            else:
                label = self.widget(0).findChild(QtWidgets.QLabel)
                if label:
                    label.setText(text)
                self.setCurrentIndex(0)

    def set_image(self, pixmap_path):
        """ Set image and fade. """
        if self._pixmap_path != pixmap_path:
            # app crashes if nonvisible elements are animated
            self._fade_disabled = False
            if not self.isVisible():
                self._fade_disabled = True

            if self.currentIndex() == 0:
                label_1 = self.widget(1).findChild(QtWidgets.QLabel)
                if label_1:
                    label_1.setPixmap(QtGui.QPixmap(pixmap_path))
                self.setCurrentIndex(1)
            else:
                label_0 = self.widget(0).findChild(QtWidgets.QLabel)
                if label_0:
                    label_0.setPixmap(QtGui.QPixmap(pixmap_path))
                self.setCurrentIndex(0)
            self._pixmap_path = pixmap_path

    def setCurrentIndex(self, index):  # pylint: disable=invalid-name
        """ Sets the active index of the stack and animates the fade. Override. """
        if index != self.currentIndex():
            if not self._fade_disabled:
                self._fader_widget = FaderWidget(
                    self.currentWidget(), self.widget(index))
            QtWidgets.QStackedWidget.setCurrentIndex(self, index)
