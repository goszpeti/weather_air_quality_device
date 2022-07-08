#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of WAQD
# (see https://github.com/goszpeti/WeatherAirQualityDevice).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import threading
import time

from typing import Optional

from waqd.base.logger import Logger
from waqd.base.component_reg import ComponentRegistry
from waqd.base.network import Network
from waqd.base.signal import QtSignalRegistry
from waqd.base.component_reg import CyclicComponent
from waqd.settings import Settings

class ComponentController():
    """ Loader, unloader and watchdog for components. """
    UPDATE_TIME = 5

    def __init__(self, settings: Settings):
        self._components = ComponentRegistry(settings)

        # thread for watchdog
        self._watch_thread: Optional[threading.Thread] = None # re-usable thread, assignment is in init_all
        self._stop_event = threading.Event()  # own stop event for watchdog
        # thread for waiting for comps unload
        self._unload_thread: Optional[threading.Thread] = None # re-usable thread, assignment is in unload_all

    @property
    def all_ready(self) -> bool:
        """ Signals, that all modules have been started loading """
        all_ready = False
        for comp_name in self._components.get_names():
            component = self._components.get(comp_name)
            if component:
                all_ready |= component.is_ready
        return all_ready

    @property
    def all_unloaded(self) -> bool:
        """ All managed modules are unloaded. """
        if not self._unload_thread:
            return True
        return not self._unload_thread.is_alive()

    @property
    def components(self) -> ComponentRegistry:
        """ Returns held components for higher level functions """
        return self._components

    def init_all(self):
        """
        Start every managed module, by starting the watch thread.
        """
        if self._unload_thread and self._unload_thread.is_alive():
            self._unload_thread.join()
        self._stop_event.clear()
        Logger().info("Start initializing all components")
        self._watch_thread = threading.Thread(name="Watchdog", target=self._watchdog_loop, daemon=True)
        self._watch_thread.start()

    def unload_all(self, reload_intended=False, updating=False):
        """
        Start unloading modules. modules_unloaded signals finish.
        """
        self._components.set_unload_in_progress()
        QtSignalRegistry().clear_registry()
        Logger().info("Start unloading all components")
        self._unload_thread = threading.Thread(
            name="UnloadModules", target=self._unload_all_components, args=[reload_intended, updating])
        self._unload_thread.start()

    def stop(self):
        """
        Stop this module, by sending a stop request.
        Actual stop is asynchronous.
        """
        if self._watch_thread and self._watch_thread.is_alive():
            self._stop_event.set()

    def _watchdog_loop(self):
        time.sleep(2)  # wait for execution
        self._components.show()

        ticker = threading.Event()
        while not ticker.wait(self.UPDATE_TIME):
            if self._stop_event.is_set():
                self._stop_event.clear()
                return
            self._components.show()
            self._watch_components()

    def _watch_components(self):
        """
        Checks existence of global variable of each module and starts it.
        """
        # check and restart wifi
        #if RuntimeSystem().is_target_system:
        Network().check_internet_connection()

        try:
            for comp_name in self._components.get_names():
                component = self._components.get(comp_name)
                if not component:
                    break
                if issubclass(type(component), CyclicComponent):
                    if component.is_ready and not component.is_alive and not component.is_disabled:
                        # call stop, so it will be initialized in the next cycle
                        self._components.stop_component(comp_name)

            sensors_to_remove = []
            for sensor_name in self._components.get_sensors():
                sensor = self._components.get_sensors()[sensor_name]
                if not sensor:
                    break
                if isinstance(sensor, CyclicComponent) and sensor.is_ready and not sensor.is_alive:
                    sensors_to_remove.append(sensor_name)
            for sensor_name in sensors_to_remove:
                self._components.get_sensors().pop(sensor_name)
        except Exception as e:
            Logger().debug(f"ERROR: Watchdog crashed: {str(e)}")


    def _unload_all_components(self, reload_intended, updating):
        """
        Stop own watcher and unload modules.
        :param reload_intended: singals, that objects, which forbid reload will be skipped
        """
        # watch threads needs to stop - updater runs continously
        self.stop()
        if self._watch_thread:
            self._watch_thread.join()

        for comp_name in self._components.get_names():
            if updating:  # exclude updater
                if self._components.auto_updater == self._components.get(comp_name):
                    continue
            self._components.stop_component(comp_name, reload_intended)
        Logger().info("ComponentRegistry: All components unloaded.")
        self._components.set_unload_finished()
