import os
import threading
import time

from piweather.base.logger import Logger
from piweather.base.components import ComponentRegistry
from piweather.base.system import RuntimeSystem
from piweather.base.components import CyclicComponent


class ComponentController():
    """ Loader, unloader and watchdog for components. """
    UPDATE_TIME = 5

    def __init__(self, settings: "Settings"):
        self._components = ComponentRegistry(settings)
        self._logger = Logger()
        self._runtime_system = RuntimeSystem()

        self._all_initialized = False
        self._wlan_failed = 0  # internal counter for wlan restart
        self._watch_thread: threading.Thread = None  # thread for watchdog
        self._stop_event = threading.Event()  # own stop event for watchdog
        self._unload_thread: threading.Thread = None  # thread for waiting for comps unload

    @property
    def all_initialized(self) -> bool:
        """ Signals, that all modules have been started loading """
        return self._all_initialized

    @property
    def all_ready(self) -> bool:
        """ Signals, that all modules have been started loading """
        all_ready = False
        for comp_name in self._components.get_names():
            component = self._components.get(comp_name)
            all_ready |= component.is_ready
        return all_ready

    @property
    def all_unloaded(self) -> bool:
        """ All managed modules are unloaded. """
        if not self._unload_thread:
            return False
        return not self._unload_thread.is_alive()

    @property
    def components(self) -> ComponentRegistry:
        """ Returns held components for higher level functions """
        return self._components

    def init_all(self):
        """
        Start every managed module, by starting the watch thread.
        """
        if self._unload_thread:
            self._unload_thread.join()
        self._stop_event.clear()
        self._logger.info("Start initializing all components")
        self._watch_thread = threading.Thread(name="Watchdog",
                                              target=self._watchdog_loop, daemon=True)
        self._watch_thread.start()

    def unload_all(self, reload_intended=True):
        """
        Start unloading modules. modules_unloaded signals finish.
        """
        self._all_initialized = False
        self._components.set_unload_in_progress()
        self._logger.info("Start unloading all components")
        self._unload_thread = threading.Thread(name="UnloadModules",
                                               target=self._wait_for_unload_components,
                                               args=[reload_intended, ])
        self._unload_thread.start()

    def stop(self):
        """
        Stop this module, by sending a stop request.
        Actual stop is asyncron.
        """
        if self._watch_thread.is_alive():
            self._stop_event.set()

    def _watchdog_loop(self):
        time.sleep(2)  # wait for execution
        self._components.show()

        self._all_initialized = True
        self._logger.info("ComponentRegistry: All components initialized")
        ticker = threading.Event()
        while not ticker.wait(self.UPDATE_TIME):
            if self._stop_event.is_set():
                self._stop_event.clear()
                return
            self._watch_components()

    def _check_wlan(self):
        """
        RPi fails often when WLAN conncetion is unstable.
        The restart of the adapter is black voodo magic, which is attempted after the second failure.
        If that doesn't help, the RPi reboots on the next failure.
        """
        if self._wlan_failed == 2:
            self._logger.error("Watchdog: Restarting wlan...")
            os.system("sudo systemctl restart dhcpcd")
            time.sleep(2)
            os.system("wpa_cli -i wlan0 reconfigure")
            os.system("sudo dhclient")
            time.sleep(5)
        # failed 3 times straight - restart linux
        if self._wlan_failed == 3:
            self._logger.error("Watchdog: Restarting system - wlan failure...")
            self._runtime_system.restart()
        [ipv4, ipv6] = self._runtime_system.get_ip()
        if not ipv4 and not ipv6:
            self._wlan_failed += 1
            time.sleep(5)
        else:
            self._wlan_failed = 0

    def _watch_components(self):
        """
        Checks existence of global variable of each module and starts it.
        """
        # TODO tries to often, if module can't init itself
        # check and restart wifi - TODO: instable, and doesnt't work if on cable
        if self._runtime_system.is_target_system:
            self._check_wlan()

        for comp_name in self._components.get_names():
            component = self._components.get(comp_name)
            if issubclass(type(component), CyclicComponent):
                if component.is_ready and not component.is_alive and not component.is_disabled:
                    # call stop, so it will be initialized in the next cycle
                    self._components.stop_component(comp_name)

    def _wait_for_unload_components(self, reload_intended=False):
        """
        Stop own watcher and unload modules.
        param reload_intended: singals, that objects, which forbid reload will be skipped
        """
        # watch threads needs to stop - updater runs continously
        self.stop()
        self._watch_thread.join()

        for comp_name in self._components.get_names():
            self._components.stop_component(comp_name, reload_intended)
        self._logger.info("ComponentRegistry: All components unloaded")
        self._components.set_unload_finished()
