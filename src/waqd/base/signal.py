from typing import TYPE_CHECKING, Any, Callable, Dict, List
from waqd.base.logger import Logger

if TYPE_CHECKING:
    from PyQt5.QtCore import pyqtBoundSignal
    
class Cbk2QtSignal():

    def __init__(self, cbk: Callable, signal: "pyqtBoundSignal") -> None:
        self.cbk = cbk
        self.signal = signal

class QtSignalRegistry():
    """ This class acts as a dependency decoupling for messaging
    between Qt Signals and non Qt builtin threads and callbacks.
    This should only be called from the GUI!
    """
    _instance = None
    _sig_dict: Dict[str, Cbk2QtSignal] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_callback(self, name, signal, target_func):
        if not self._sig_dict.get(name, None):
            self._sig_dict[name] = Cbk2QtSignal(target_func, signal)
        self._sig_dict[name].signal.connect(target_func)

    
    def emit_sig_callback(self, name, *args):
        try:
            if args:
                self._sig_dict[name].signal.emit(args)
            else:
                self._sig_dict[name].signal.emit()
        except:
            Logger().warning(f"Can't emit signal {name}")
            
    def clear_registry(self):
        self._sig_dict.clear()

    # def emit_conan_pkg_signal_callback(self, conan_ref, pkg_id):
    #     if not self.conan_pkg_installed:
    #         return
    #     self.conan_pkg_installed.emit(conan_ref, pkg_id)
