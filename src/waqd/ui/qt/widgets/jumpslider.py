
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
