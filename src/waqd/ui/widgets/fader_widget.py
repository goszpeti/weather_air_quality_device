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


class FaderWidget(QtWidgets.QWidget):
    """
    Creates custom widget to fade between two widgets.
    """

    def __init__(self, old_widget, new_widget, length=666):
        """
        It has to be assigned to a variable.
        Length is in ms.
        """
        QtWidgets.QWidget.__init__(self, new_widget)

        self.old_pixmap = QtGui.QPixmap(new_widget.size())
        old_widget.render(self.old_pixmap)
        self.pixmap_opacity = 1.0

        self.timeline = QtCore.QTimeLine()
        self.timeline.valueChanged.connect(self.animate)
        self.timeline.finished.connect(self.close)
        self.timeline.setDuration(length)
        self.timeline.start()

        self.resize(new_widget.size())
        self.show()

    def paintEvent(self, event):  # pylint: disable=unused-argument,invalid-name
        """ callback from animate - repaint sets the actual image """
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setOpacity(self.pixmap_opacity)
        painter.drawPixmap(0, 0, self.old_pixmap)
        painter.end()

    def animate(self, value):
        """ decreases opacity for fade effect """
        self.pixmap_opacity = 1.0 - value
        self.repaint()
