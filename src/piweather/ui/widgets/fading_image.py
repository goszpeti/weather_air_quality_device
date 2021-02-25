from PyQt5 import QtGui, QtWidgets

from .fader_widget import FaderWidget


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
        return label.text()

    def set_text(self, text):
        """ Set text to the visible child label """
        if self.text != text:
            # app crashes if nonvisible elements are animated
            self._fade_disabled = False
            if not self.isVisible():
                self._fade_disabled = True

            if self.currentIndex() == 0:
                label = self.widget(1).findChild(QtWidgets.QLabel)
                label.setText(text)
                self.setCurrentIndex(1)
            else:
                label = self.widget(0).findChild(QtWidgets.QLabel)
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
                label_1.setPixmap(QtGui.QPixmap(pixmap_path))
                self.setCurrentIndex(1)
            else:
                label_0 = self.widget(0).findChild(QtWidgets.QLabel)
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
