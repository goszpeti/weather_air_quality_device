
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

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.deleteLater()
        return super().closeEvent(a0)

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
