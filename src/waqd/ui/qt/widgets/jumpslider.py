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
from PyQt5 import QtWidgets


class JumpSlider(QtWidgets.QSlider):
    """
    A touch optimized slider, which sets the value on the absolute position where the mouse
    clicked on the slider.
    """

    def _jump_to_nearest_tick(self, event):
        """ Sets the position to the position of the mouse. """
        slider_value = QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(),
                                                         event.x(), self.width())
        # round the current location, so that it falls to the nearest tick
        tick_interval = self.tickInterval()
        slider_value = round(slider_value/tick_interval) * tick_interval
        self.setValue(slider_value)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """ Override to fix the react on click. """
        self._jump_to_nearest_tick(event)

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """ Override to react on pulling the silder around. """
        self._jump_to_nearest_tick(event)
