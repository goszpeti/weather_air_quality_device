from PyQt5 import QtWidgets


class JumpSlider(QtWidgets.QSlider):
    """
    A touch optimized slider, which sets the value on the absolute position where the mouse
    clicked on the slider.
    """

    def _fix_position_to_interval(self, event):
        """ Sets the position to the position of the mouse. """
        # get the value from the slider
        value = QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(),
                                                         event.x(), self.width())

        # get the desired tick interval from the slider
        tick_interval = self.tickInterval()

        # convert the value to be only at the tick interval locations
        value = round(value/tick_interval) * tick_interval

        # set the position of the slider based on the interval position
        self.setValue(value)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """ Override to fix the react on click. """
        self._fix_position_to_interval(event)

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """ Override to react on pulling the silder around. """
        self._fix_position_to_interval(event)
