
import abc

from typing import TYPE_CHECKING, Callable
from PyQt5 import QtCore

from waqd.base.file_logger import Logger

if TYPE_CHECKING:
    from waqd.ui.qt.main_window import WeatherMainUi
    from waqd.settings import Settings
    from waqd.ui.qt.qt.weather_ui import Ui_MainWindow

class WorkerObject(QtCore.QObject):

    def __init__(self, target: Callable, parent = None):
        super(self.__class__, self).__init__(parent)
        self.target = target
        
    def run(self):
        self.target()

class SubUi(metaclass=abc.ABCMeta):
    """
    Common class for all ui modules, which have a different update time.
    """
    UPDATE_TIME = 1000  # microseconds

    def __init__(self, parent: "WeatherMainUi", ui: "Ui_MainWindow", settings: "Settings"):
        self._main_ui = parent
        self._ui = ui
        self._logger = Logger()
        self._settings = settings

        # set up update thread
        self._update_timer = QtCore.QTimer(parent)
        self._update_timer.setObjectName("Update" + repr(self).split(" ")[0])
        self._update_timer.timeout.connect(self._cyclic_update)
        self._update_timer.start(self.UPDATE_TIME)
        self._first_thread = QtCore.QThread(self._main_ui)

    def init_with_cyclic_update(self):
        self._first_thread.setObjectName("Init" + repr(self).split(" ")[0])
        self.worker = WorkerObject(target=self._cyclic_update)
        self.worker.moveToThread(self._first_thread)
        self._first_thread.started.connect(self._cyclic_update)  # self.worker.run)
        self._first_thread.start()
  
    @abc.abstractmethod
    def _cyclic_update(self):
        """ implement ui update callback here """
        raise NotImplementedError('Users must define _cyclic_update to use this base class')

    def stop(self):
        """ Stop the update loop. """
        if self._first_thread.isRunning():
            self._first_thread.quit()
        if self._update_timer.isActive():
            self._update_timer.stop()
