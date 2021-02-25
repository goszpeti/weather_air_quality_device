
from PyQt5 import QtCore, QtWidgets


class ClickableLabel(QtWidgets.QLabel):
    """ Qt label, which can react on a mouse click. Used for detail views. """
    # overrides base QT behaviour. Needs to be a class variable.
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Callback to emitting the clicked signal, so "clicked" can be used to connect any function. """
        self.clicked.emit()
