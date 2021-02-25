from PyQt5 import QtCore, QtGui, QtWidgets

from piweather import config
from piweather.resources import get_rsc_file

# define Qt so it can be used like the namespace in C++
Qt = QtCore.Qt


class SplashScreen(QtWidgets.QSplashScreen):
    """
    Generic splashcreen. Must always be spawned in a new thread, while the original thread
    executes qt_app.processEvents() in a while loop, until it should be stopped.
    """

    def __init__(self, movie: QtGui.QMovie, background=True):
        """
        param movie: a movie (can be a gif for loading) to be played continously
        background: set the image as the background.
        The layout changes if background ist set.
        Without: the movie plays in the middle. A screenshot is taken when the splashcreen
        initializes and set as background, so changing elements in the gui are not seen by the user.
        With: background image is scaled and movie plays in the bottom middle.
        """
        self._movie = movie
        self._is_background_set = background

        movie.jumpToFrame(0)
        if background:
            pixmap = QtGui.QPixmap(str(get_rsc_file("gui_base", "loading")))
            pixmap = pixmap.scaled(800, 480, transformMode=Qt.SmoothTransformation)
        else:
            screen = config.qt_app.primaryScreen()
            pixmap = screen.grabWindow(0)

        QtWidgets.QSplashScreen.__init__(self, pixmap)
        if config.DEBUG_LEVEL == 0:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self._movie.frameChanged.connect(self.repaint)

    def mousePressEvent(self, event):  # pylint: disable=unused-argument, invalid-name, no-self-use
        """ Do nothing on mouse click. Otherwise it disappears. """
        return

    def showEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Start movie, when it is shown. """
        self._movie.start()

    def hideEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Stop movie, when it is hidden. """
        self._movie.stop()

    def paintEvent(self, event):  # pylint: disable=unused-argument, invalid-name
        """ Callback for paint event from self.repaint. Sets the animation for every frame. """
        pixmap = self._movie.currentPixmap()
        painter = QtGui.QPainter(self)
        if self._is_background_set:
            pixmap = pixmap.scaledToWidth(70, mode=Qt.SmoothTransformation)
            painter.drawPixmap(int(self.width()/2 - pixmap.width()/2),
                               int(self.height() - pixmap.height() - 10), pixmap)
        else:
            pixmap = pixmap.scaledToWidth(200, mode=Qt.SmoothTransformation)
            painter.drawPixmap(int(self.width()/2 - pixmap.width()/2),
                               int(self.height()/2 - pixmap.height()/2), pixmap)

    def sizeHint(self):  # pylint: disable=invalid-name
        """ Set the size to scaled size of the movie. """
        return self._movie.scaledSize()
