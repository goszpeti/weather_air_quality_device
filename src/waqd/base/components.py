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
import types
# this allows to use forward declarations to avoid circular imports
from typing import TYPE_CHECKING, Callable, Dict, List, Union, Optional, Type

from waqd.base.logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.settings import (BME_280_ENABLED, BMP_280_ENABLED, DHT_22_DISABLED, CCS811_ENABLED,
                           DHT_22_PIN, MH_Z19_ENABLED, MOTION_SENSOR_ENABLED,
                           MOTION_SENSOR_PIN, Settings)

if TYPE_CHECKING:
    from waqd.components import (Display, ESaver, EventHandler, TextToSpeach, Sound, OpenWeatherMap, SR501,
                                 OnlineUpdater, TempSensor, TvocSensor, BarometricSensor, HumiditySensor,
                                 CO2Sensor, DustSensor, LightSensor, Prologue433)

class Component:
    """ Base class for all components """

    def __init__(self, components: "ComponentRegistry" = None, settings: Settings = None):
        self._comps = components
        self._settings = settings
        self._logger = Logger()
        self._runtime_system = RuntimeSystem()
        self._reload_forbidden = False  # must be set manually in the child class
        self._disabled = False
        self._ready = True

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

    def __init__(self, components=None, settings=None):
        super().__init__(components, settings)
        self._ticker_event = threading.Event()
        self._update_thread: Optional[threading.Thread] = None
        self._ready = False
        self._error_num = 0

    @property
    def is_alive(self):
        """ Update thread is running, module is OK. """
        if not self._update_thread:
            return False
        if self._update_thread.is_alive() and not self._ticker_event.is_set():
            return True
        return False

    def stop(self):
        """ Stop this module, by sending a stop request. """
        if self._update_thread:
            self._ticker_event.set()
            if self._update_thread.is_alive():
                self._update_thread.join(self.STOP_TIMEOUT)

    def _start_update_loop(self, init_func: Callable = None,
                           update_func: Callable = None):
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
                self._is_disabled = True
                return
            update_func()


class ComponentRegistry():
    """
    Abstraction to hold all components, create, stop and get access to them.
    An instance is passed automatically to all components.
    """
    # Constants for Component names to an alternitave method to access components
    
    comp_init_lock = threading.RLock() # lock to only instantiate one component at a time

    def __init__(self, settings: Settings):
        self._logger = Logger()
        self._settings = settings
        self._unload_in_progress = False  # don't generate new objects
        self._components: Dict[str, Component] = {}  # holds all the instances
        self._sensors: Dict[str, CyclicComponent] = {}  # mapping from components to specific sensor types
        self._stop_thread: threading.Thread

    def set_unload_in_progress(self):
        """ Signals the components, that they are unloading and should not instantiate new objects. """
        self._unload_in_progress = True

    def set_unload_finished(self):
        """ Signals the components, that unload finished and business is back as usual. """
        # reset sensors
        self._sensors = {}
        self._unload_in_progress = False

    def get_names(self) -> List[str]:
        """ Get a list of names of all components"""
        return list(self._components)

    def get(self, name) -> Union[Component, CyclicComponent, None]:
        """ Get a specific component instance """
        return self._components.get(name)

    def stop_component_instance(self, instance):
        """
        Stops a component based on an instance. 
        This is meant for a component to commit sudoko, e.g. when for restarting itself.
        """
        for comp in self._components:
            if instance is self._components[comp]:
                # cant stop from own instance
                self._stop_thread = threading.Thread(name="Stop" + comp,
                                                     target=self.stop_component,
                                                     args=[comp, ],
                                                     daemon=True)
                self._stop_thread.start()
                break
        # also remove sensor instances
        for sensor in self._sensors:
            if instance is self._sensors[sensor]:
                self._sensors.pop(sensor)
                break

    def stop_component(self, name, reload_intended=False):
        """ Stops a component. CyclicComponentRegistry can take some time. """
        component = self._components.pop(name)
        if not component:
            return
        # don't do anything, when reload is intended and the component forbids it
        if reload_intended and component.reload_forbidden:
            return

        # call stop, if module is threaded
        if isinstance(component, CyclicComponent):
            self._logger.info("ComponentRegistry: Stopping %s", name)
            component.stop()
        # call destructors
        del component

    def show(self):
        """ Check all components and thus initialize them """
        return [self.display, self.sound, self.auto_updater, self.tts, self.temp_sensor, self.humidity_sensor,
                self.tvoc_sensor, self.pressure_sensor, self.co2_sensor, self.remote_temp_sensor,
                self.motion_detection_sensor, self.energy_saver, self.weather_info, self.event_handler]

    @property
    def display(self) -> "Display":
        """ Access for Display singleton """
        from waqd.components.display import Display  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(Display, [self._settings])

    @property
    def event_handler(self) -> "EventHandler":
        """ Access for Greeter singleton """
        from waqd.components.events import EventHandler  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(EventHandler, [self, self._settings])

    @property
    def tts(self) -> "TextToSpeach":
        """ Access for TTS singleton """
        from waqd.components.speech import TextToSpeach  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(TextToSpeach, [self, self._settings])

    @property
    def sound(self) -> "Sound":
        """ Access for Sound singleton """
        from waqd.components.sound import Sound  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(Sound, [self._settings])

    @property
    def energy_saver(self) -> "ESaver":
        """ Access for ESaver singleton """
        from waqd.components.power import ESaver  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(ESaver, [self, self._settings])

    @property
    def weather_info(self) -> "OpenWeatherMap":
        """ Access for OnlineWeather singleton """
        from waqd.components.online_weather import OpenWeatherMap  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(OpenWeatherMap, [self._settings])

    @property
    def auto_updater(self) -> "OnlineUpdater":
        """ Access for OnlineUpdater singleton """
        from waqd.components.updater import OnlineUpdater  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(OnlineUpdater, [self, self._settings])

    @property
    def temp_sensor(self) -> "TempSensor":
        """ Access for temperature sensor  """
        internal_name = "TempSensor"
        sensor: "TempSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            dht22_pin = self._settings.get(DHT_22_PIN)
            if dht22_pin != DHT_22_DISABLED:
                sensor = self.create_component_instance(sensors.DHT22, [dht22_pin, self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self.create_component_instance(sensors.BME280, [self, self._settings])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self.create_component_instance(sensors.BMP280, [self, self._settings])
            else:  # create a default instance that is disabled, so the watchdog
                # won't try to instantiate a new one over and over
                sensor = self.create_component_instance(sensors.TempSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_temp = True
        return sensor

    @property
    def humidity_sensor(self) -> "HumiditySensor":
        """ Access for humidity sensor """
        internal_name = "HumiditySensor"
        sensor: "HumiditySensor" = self._sensors.get(internal_name)
        if not sensor:
            # DHT-22 is prioritized, if both are available
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            dht22_pin = self._settings.get(DHT_22_PIN)
            if dht22_pin != DHT_22_DISABLED:
                sensor = self.create_component_instance(sensors.DHT22, [dht22_pin, self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self.create_component_instance(sensors.BME280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.HumiditySensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_hum = True
        return sensor

    @property
    def pressure_sensor(self) -> "BarometricSensor":
        """ Access for pressure sensor """
        internal_name = "BarometricSensor"
        sensor: "BarometricSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            if self._settings.get(BME_280_ENABLED):
                sensor = self.create_component_instance(sensors.BME280, [self, self._settings])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self.create_component_instance(sensors.BMP280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.BarometricSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_pres = True
        return sensor

    @property
    def co2_sensor(self) -> "CO2Sensor":
        """ Access for air_quality_sensor """
        internal_name = "CO2Sensor"
        sensor: "CO2Sensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            # MH_Z19 is prioritized, if both are available
            if self._settings.get(MH_Z19_ENABLED):
                sensor = self.create_component_instance(sensors.MH_Z19, [self._settings])
            elif self._settings.get(CCS811_ENABLED):
                sensor = self.create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.CO2Sensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_co2 = True
        return sensor

    @property
    def tvoc_sensor(self) -> "TvocSensor":
        """ Access for air_quality_sensor """
        internal_name = "TVOCSensor"
        sensor: "TvocSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            if self._settings.get(CCS811_ENABLED):
                sensor = self.create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.TvocSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_tvoc = True
        return sensor

    @property
    def dust_sensor(self) -> "DustSensor":
        """ Access for dust sensor """
        internal_name = "DustSensor"
        sensor: "DustSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            # if self._settings.get(GP2Y1010AU0F_ENABLED):
            #     sensor = self.create_component_instance(sensors.GP2Y1010AU0F, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self.create_component_instance(sensors.DustSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_dust = True
        return sensor

    @property
    def light_sensor(self) -> "LightSensor":
        """ Access for light sensor """
        internal_name = "LightSensor"
        sensor: "LightSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            # if self._settings.get(CGY302_ENABLED):
            #     sensor = self.create_component_instance(sensors.GY302, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self.create_component_instance(sensors.LightSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.log_light = True
        return sensor

    @property
    def motion_detection_sensor(self) -> "SR501":
        """ Access for motion_detection_sensor singleton """
        internal_name = "MotionSensor"
        sensor: "SR501" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors  # pylint: disable=import-outside-toplevel
            pin = self._settings.get(MOTION_SENSOR_PIN)
            if self._settings.get(MOTION_SENSOR_ENABLED) and pin > 0:
                sensor = self.create_component_instance(sensors.SR501, [pin])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.SR501, [0])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def remote_temp_sensor(self) -> "Prologue433":
        """ Access for remote_temp_sensor singleton """
        from waqd.components.sensors import Prologue433  # pylint: disable=import-outside-toplevel
        return self.create_component_instance(Prologue433, [self._settings])

    def create_component_instance(self, class_ref: Type[Component], args: List = [], name_ref=None) -> Union[Component, CyclicComponent]:
        """ Generic method for component creation and access. """
        name: str = class_ref.__name__
        if name_ref:
            name = name_ref
        with self.comp_init_lock:
            component = self._components.get(name)
            if component:
                return component

            if component is None and not self._unload_in_progress:
                self._logger.info("ComponentRegistry: Starting %s", name)

                if issubclass(class_ref, Component):
                    new_component = class_ref(*args)
                    self._components.update({name: new_component})
                else:
                    raise TypeError("The component " + str(class_ref) +
                                    " to be created must be subclass of 'Component', but is instead a " +
                                    class_ref.__class__.__name__ + " .")
                return new_component
