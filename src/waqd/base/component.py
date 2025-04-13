


import threading
import time
import types
# this allows to use forward declarations to avoid circular imports
from typing import TYPE_CHECKING, Callable, Optional

from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import Settings

if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry


class Component:
    """ Base class for all components """

    def __init__(self, components: Optional["ComponentRegistry"]=None, settings: Optional[Settings]=None, enabled=True):
        self._comps = components
        self._settings = settings  # TODO remove
        self._logger = Logger()
        self._runtime_system = RuntimeSystem()
        self._reload_forbidden = False  # must be set manually in the child class
        self._disabled = not enabled
        self._ready = False

    @property
    def is_ready(self) -> bool:
        """ Returns true, if component is ready to be used."""
        return self._ready

    @property
    def reload_forbidden(self):
        """
        When this flag is set, the component signals, that it should not be reloaded,
        when settings change. This should only be used by components, which use
        read-only settings and need a long time to initialize.
        """
        return self._reload_forbidden

    @property
    def is_disabled(self):
        """
        The component can signal it is disabled, if it does not work correctly
        and its values are not to be used. (Component will always return an instance)
        """
        return self._disabled

    def stop(self):
        """ Stop this component. """
        pass


class CyclicComponent(Component):
    """
    Implements the cyclic updatefor a Component with a separate thread.
    State can be checked by is_alive.
    """
    UPDATE_TIME: int = 0  # in seconds
    INIT_WAIT_TIME: int = 0  # in seconds
    STOP_TIMEOUT: int = 2 * UPDATE_TIME
    MAX_ERROR = 5  # max error before reset

    def __init__(self, components=None, settings=None, enabled=True):
        super().__init__(components, settings, enabled)
        self._ticker_event = threading.Event()
        self._update_thread: Optional[threading.Thread] = None
        self._ready = False
        self._error_num = 0
        if settings: # for type hinting
            self._settings: Settings


    @property
    def is_alive(self) -> bool:
        """ Update thread is running, module is OK. """
        if not self._update_thread:
            return False
        if self._update_thread.is_alive() and not self._ticker_event.is_set():
            return True
        return False

    def stop(self):
        """ Stop this component, by sending a stop request. """
        if self._update_thread:
            self._ticker_event.set()
            if self._update_thread.is_alive():
                self._update_thread.join(self.STOP_TIMEOUT)

    def _start_update_loop(self, init_func: Optional[Callable]=None,
                           update_func: Optional[Callable]=None):
        """
        Generic set up function for cyclic thread.
        Has to be called with own init and update function in child class.
        """
        self._update_thread = threading.Thread(name=self.__class__.__name__,
                                               target=self._update_loop,
                                               args=[init_func, update_func, ],
                                               daemon=True)
        self._update_thread.start()

    def _update_loop(self, init_func: types.FunctionType, update_func: types.FunctionType):
        """
        Executes an initializer function, optionally waits
        and then calls the update function periodically.
        """
        time.sleep(self.INIT_WAIT_TIME)
        if init_func:
            init_func()
        self._ready = True
        while not self._ticker_event.wait(self.UPDATE_TIME):
            if self._ticker_event.is_set():
                self._ticker_event.clear()
                return
            if self._error_num == self.MAX_ERROR:
                self._disabled = True
                return
            update_func()
