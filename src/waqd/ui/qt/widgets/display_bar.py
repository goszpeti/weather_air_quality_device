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
from PyQt5.QtCore import Qt

from waqd.ui.qt.widgets import ClickableLabel
from waqd.ui.qt.common import get_font


class DisplayBar(ClickableLabel):
    WIDTH = 290  # pixel - this is the original non scaled value, not the same as self.width
    HEIGHT = 51  # pixel
    TYPE_LABEL_OFFSET = 20  # pixel to the left
    TYPE_LABEL_REL_SIZE = 1/3
    VALUE_STYLE_SHEET = "QLabel{background-color: transparent;color: %s;}"

    def __init__(self, parent, color="#FFFFFF", type_text="N/A", font_size=24):
        super().__init__(parent=parent)
        self._font_size = font_size
        # for high dpi scaling
        self._pixel_ratio = QtWidgets.QApplication.instance().devicePixelRatio()

        self._value_label = QtWidgets.QLabel(self)
        self._value_label.setText("N/A")

        self._type_label = QtWidgets.QLabel(self)
        self._type_label.setText(type_text)

        self.draw_box(color, color)

        self._type_label.setGeometry(self.x() + self.TYPE_LABEL_OFFSET, self.y(),
                                     int(self.WIDTH * self.TYPE_LABEL_REL_SIZE), self.HEIGHT)
        self._type_label.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self._type_label.setStyleSheet("QLabel{color: rgb(255, 255, 255)}")
        self._type_label.setAlignment(Qt.AlignmentFlag(Qt.AlignLeft | Qt.AlignVCenter))
        self._type_label.setObjectName(type_text)

        extra_margin = 5
        self._value_label.setGeometry(int(self.x() + self.WIDTH * self.TYPE_LABEL_REL_SIZE), self.y(),
                                      int(self.WIDTH * (1 - self.TYPE_LABEL_REL_SIZE) -
                                          self.TYPE_LABEL_OFFSET - extra_margin),
                                      self.HEIGHT)
        self._value_label.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self._value_label.setStyleSheet("QLabel{color: rgb(255, 255, 255)}")
        self._value_label.setAlignment(Qt.AlignmentFlag(Qt.AlignRight | Qt.AlignVCenter))
        self._value_label.setObjectName(type_text + "_value")

    def set_value_label(self, text: str, color="white"):
        self._value_label.setStyleSheet(self.VALUE_STYLE_SHEET % color)
        return self._value_label.setText(text)

    def setup_attributes(self, color: str, stop_color: str, type_text: str, font_size: int, font_name: str):
        self._type_label.setText(type_text)
        self.draw_box(color, stop_color)

        font = get_font(font_name)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        font.setPointSize(font_size)
        self._type_label.setFont(font)
        self._value_label.setFont(font)
        # if setup is called, the bar will be displayed
        self.show()

    def draw_box(self, color: str, stop_color: str):
        self.canvas = QtGui.QPixmap(int(self.WIDTH * self._pixel_ratio), int(self.HEIGHT * self._pixel_ratio))
        self.canvas.fill(Qt.transparent)
        self.canvas.setDevicePixelRatio(self._pixel_ratio)

        painter = QtGui.QPainter(self.canvas)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, True)

        gradient = QtGui.QLinearGradient(150, self.HEIGHT/2, self.WIDTH, self.HEIGHT/2)
        gradient.setColorAt(0, QtGui.QColor(color))
        gradient.setColorAt(1, QtGui.QColor(stop_color))
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(Qt.transparent))
        brush = QtGui.QBrush(gradient)
        brush.setStyle(Qt.LinearGradientPattern)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(QtCore.QRectF(10, 0, self.WIDTH, self.HEIGHT), 25, 25)
        painter.end()

        self.setPixmap(self.canvas)
