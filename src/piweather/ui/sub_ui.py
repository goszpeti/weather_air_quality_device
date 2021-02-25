import abc

from PyQt5 import QtCore

from piweather.base.logger import Logger
from piweather.base.components import ComponentRegistry


class SubUi(metaclass=abc.ABCMeta):
    """
    Common class for all ui modules, which have a different update time.
    """
    UPDATE_TIME = 1000  # microseconds

    def __init__(self, main_ui: QtCore.QObject, settings):
        self._main_ui = main_ui
        self._ui = main_ui.ui
        self._comps: ComponentRegistry = main_ui._comps
        self._logger = Logger()
        self._settings = settings

        # set up update thread
        self._update_timer = QtCore.QTimer(main_ui)
        self._update_timer.timeout.connect(self._cyclic_update)
        self._update_timer.start(self.UPDATE_TIME)

    @abc.abstractmethod
    def _cyclic_update(self):
        """ implement ui update callback here """
        raise NotImplementedError('Users must define _cyclic_update to use this base class')

    def stop(self):
        """ Stop the update loop. """
        self._update_timer.stop()
