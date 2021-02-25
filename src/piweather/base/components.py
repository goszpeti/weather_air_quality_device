import threading
import time
import types

from piweather.base.logger import Logger
from piweather.base.system import RuntimeSystem
from piweather.settings import (CCS811_ENABLED, MH_Z19_ENABLED, BMP_280_ENABLED, DHT_22_PIN, DHT_22_DISABLED,
                                MOTION_SENSOR_ENABLED, MOTION_SENSOR_PIN, Settings)
# this allows to use forward declarations to avoid circular imports
from typing import TYPE_CHECKING, List, Dict, Callable
if TYPE_CHECKING:
    from piweather.components import display, online_weather, power, sensors, speach, updater


class Component:
    """ Base class for all components """

    def __init__(self, components: "ComponentRegistry" = None, settings: Settings = None):
        self._comps = components
        self._settings = settings
        self._logger = Logger()
        self._runtime_system = RuntimeSystem()
        self._reload_forbidden = False  # must be set manually in the child class
        self._disabled = False  # TODO: implement behaviour, so that a disabled component is not polled constantly
        self._ready = True  # no extra steps

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

    def __init__(self, components=None, settings=None):
        super().__init__(components, settings)
        self._ticker_event = threading.Event()
        self._update_thread: threading.Thread = None
        self._ready = False

    @property
    def is_alive(self):
        """ Update thread is running, module is OK. """
        if not self._update_thread:
            return False
        if self._update_thread.is_alive() and not self._ticker_event.isSet():
            return True
        return False

    def stop(self):
        """ Stop this module, by sending a stop request. """
        if self._update_thread:
            self._ticker_event.set()
            self._update_thread.join(self.STOP_TIMEOUT)

    def _start_update_loop(self, init_func: Callable = None,
                           update_func: Callable = None):
        """
        Generic set up function for cyclic thread.
        Has to be called with own init and update function in child class.
        """
        # disable multiprocessing as long as no testing concept is found
        # if config.DEBUG_LEVEL > 2:
        Process = threading.Thread
        # else:
        #    from multiprocessing import Process
        # daemon - run continously until program exists
        self._update_thread = Process(name=self.__class__.__name__,
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
            update_func()


class ComponentRegistry():
    """
    Abstraction to hold all components, create, stop and get access to them.
    An instance is passed automatically to all components.
    """
    comp_init_lock = threading.RLock()

    def __init__(self, settings: Settings):
        self._logger = Logger()
        self._settings = settings
        self._unload_in_progress = False  # don't generate new objects
        self._components: Dict[str, Component] = {}  # holds all the instances
        self._sensors: Dict[str, Component] = {}  # mapping from components to specific sensor types

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

    def get(self, name) -> Component:
        """ Get a specific component instance """
        return self._components.get(name, None)

    def stop_component_instance(self, instance):
        for comp in self._components:
            if instance is self._components[comp]:
                # cant stop from own instance
                self._stop_thread = threading.Thread(name="Stop" + comp,
                                                     target=self.stop_component,
                                                     args=[comp, ],
                                                     daemon=True)
                self._stop_thread.start()
                break

    def stop_component(self, name, reload_intended=False):
        """ Stops a component. CyclicComponentRegistry can take some time. """
        component = self._components.get(name)
        if not component:
            return
        # don't do anything, when reload is intended and the component forbids it
        if reload_intended and component.reload_forbidden:
            return

        # call stop, if module is threaded
        # if issubclass(type(component), CyclicComponent):
        self._logger.info("ComponentRegistry: Stopping %s", name)
        component.stop()
        # call destructors
        del component
        # reset dict variable to None
        self._components[name] = None

    def show(self):
        """ Check all components and thus initialize them """
        return [self.display, self.sound, self.auto_updater, self.tts, self.temp_sensor, self.humidity_sensor,
                self.tvoc_sensor, self.pressure_sensor, self.co2_sensor, self.remote_temp_sensor, self.motion_detection_sensor,
                self.energy_saver, self.weather_info, self.event_handler]

    @property
    def display(self) -> "display.Display":
        """ Access for Display singleton """
        from piweather.components.display import Display
        return self.create_component_instance(Display, [self._settings], "Display")

    @property
    def event_handler(self) -> "events.EventHandler":
        """ Access for Greeter singleton """
        from piweather.components.events import EventHandler
        return self.create_component_instance(EventHandler, [self, self._settings], "EventHandler")

    @property
    def tts(self) -> "speach.TextToSpeach":
        """ Access for TTS singleton """
        from piweather.components.speach import TextToSpeach
        return self.create_component_instance(TextToSpeach, [self, self._settings], "TTS")

    @property
    def sound(self) -> "sound.Sound":
        """ Access for Sound singleton """
        from piweather.components.sound import Sound
        return self.create_component_instance(Sound, [self._settings], "Sound")

    @property
    def energy_saver(self) -> "power.ESaver":
        """ Access for ESaver singleton """
        from piweather.components.power import ESaver
        return self.create_component_instance(ESaver, [self, self._settings], "EnergySaver")

    @property
    def weather_info(self) -> "online_weather.OpenWeatherMap":
        """ Access for OnlineWeather singleton """
        from piweather.components.online_weather import OpenWeatherMap
        return self.create_component_instance(OpenWeatherMap, [self._settings], "WeatherInfo")

    @property
    def auto_updater(self) -> "updater.OnlineUpdater":
        """ Access for OnlineUpdater singleton """
        from piweather.components.updater import OnlineUpdater
        return self.create_component_instance(OnlineUpdater, [self, self._settings], "OnlineUpdater")

    @property
    def temp_sensor(self) -> "sensors.TempSensor":
        """ Access for temperature sensor  """
        internal_name = "TempSensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            import piweather.components.sensors as sensors
            dht22_pin = self._settings.get(DHT_22_PIN)
            if dht22_pin != DHT_22_DISABLED:
                sensor = self.create_component_instance(sensors.DHT22, [dht22_pin, self])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self.create_component_instance(sensors.BMP280)
            else:  # create a default instance that is disabled, so the watchdog
                # won't try to instantiate a new one over and over
                sensor = self.create_component_instance(sensors.TempSensor, [True])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def humidity_sensor(self) -> "sensors.HumiditySensor":
        """ Access for humidity sensor """
        internal_name = "HumiditySensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            # DHT-22 is prioritized, if both are available
            import piweather.components.sensors as sensors
            dht22_pin = self._settings.get(DHT_22_PIN)
            if dht22_pin != DHT_22_DISABLED:
                sensor = self.create_component_instance(sensors.DHT22, [dht22_pin, self])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.HumiditySensor, [True])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def pressure_sensor(self) -> "sensors.BarometricSensor":
        """ Access for pressure sensor """
        internal_name = "BarometricSensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            import piweather.components.sensors as sensors
            if self._settings.get(BMP_280_ENABLED):
                sensor = self.create_component_instance(sensors.BMP280)
                self._sensors.update({internal_name: sensor})
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.BarometricSensor, [True])
        return sensor

    @property
    def co2_sensor(self) -> "sensors.CO2Sensor":
        """ Access for air_quality_sensor """
        internal_name = "CO2Sensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            import piweather.components.sensors as sensors
            # MH_Z19 is prioritized, if both are available
            if self._settings.get(MH_Z19_ENABLED):
                from piweather.components.sensors import MH_Z19
                sensor = self.create_component_instance(sensors.MH_Z19)
            elif self._settings.get(CCS811_ENABLED):
                sensor = self.create_component_instance(sensors.CCS811, [self])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.CO2Sensor, [True])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def tvoc_sensor(self) -> "sensors.TvocSensor":
        """ Access for air_quality_sensor """
        internal_name = "TVOCSensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            import piweather.components.sensors as sensors
            if self._settings.get(CCS811_ENABLED):
                from piweather.components.sensors import CCS811
                sensor = self.create_component_instance(sensors.CCS811, [self])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.TvocSensor, [True])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def motion_detection_sensor(self) -> "sensors.SR501":
        """ Access for motion_detection_sensor singleton """
        internal_name = "MotionSensor"
        sensor = self._sensors.get(internal_name)
        if not sensor:
            import piweather.components.sensors as sensors
            pin = self._settings.get(MOTION_SENSOR_PIN)
            if self._settings.get(MOTION_SENSOR_ENABLED) and pin > 0:
                sensor = self.create_component_instance(sensors.SR501, [pin])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.SR501, [0])
            self._sensors.update({internal_name: sensor})
        return sensor

    @property
    def remote_temp_sensor(self) -> "sensors.RemoteTemp":
        """ Access for remote_temp_sensor singleton """
        # TODO
        from piweather.components.sensors import Prologue433
        return self.create_component_instance(Prologue433)

    def create_component_instance(self, class_ref, args: List = [], name_ref=None) -> Component:
        """ Generic method for component creation and access. """
        name = class_ref.__name__
        if name_ref:
            name = name_ref
        with self.comp_init_lock:
            component: Component = self._components.get(name)
            if component is None and not self._unload_in_progress:
                self._logger.info("ComponentRegistry: Starting %s", name)

                if issubclass(class_ref, Component):
                    component = class_ref(*args)
                    self._components.update({name: component})
                else:
                    raise TypeError("The component " + str(class_ref) +
                                    " to be created must be subclass of 'Component', but is instead a " +
                                    class_ref.__class__.__name__ + " .")
        return component
