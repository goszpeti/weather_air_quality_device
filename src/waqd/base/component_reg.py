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
# this allows to use forward declarations to avoid circular imports
from typing import TYPE_CHECKING, Dict, List, Optional, Type, TypeVar, Union
import waqd
from waqd.base.component import Component, CyclicComponent
from waqd.base.logger import Logger
from waqd.settings import (AUTO_UPDATER_ENABLED, BME_280_ENABLED,
                           BMP_280_ENABLED, BRIGHTNESS, CCS811_ENABLED,
                           DHT_22_DISABLED, DHT_22_PIN, DISPLAY_TYPE, EVENTS_ENABLED, LANG,
                           LOCATION, MH_Z19_ENABLED, MOTION_SENSOR_ENABLED,
                           MOTION_SENSOR_PIN, NIGHT_MODE_END, OW_API_KEY, OW_CITY_IDS, REMOTE_MODE_URL, SERVER_ENABLED,
                           SOUND_ENABLED, UPDATER_USER_BETA_CHANNEL, USER_API_KEY, USER_SESSION_SECRET,
                           WAVESHARE_DISP_BRIGHTNESS_PIN, Settings)

if TYPE_CHECKING:
    from waqd.components import (SR501, BarometricSensor, CO2Sensor, Display,
                                 DustSensor, ESaver, EventHandler,
                                 HumiditySensor, LightSensor, OnlineUpdater,
                                 OpenWeatherMap, WAQDRemoteSensor, SensorComponent,
                                 Sound, TempSensor, TextToSpeach, TvocSensor, Server)


class ComponentRegistry():
    """
    Abstraction to hold all components, create, stop and get access to them.
    An instance is passed automatically to all components.
    """
    # Constants for Component names to an alternitave method to access components

    comp_init_lock = threading.Lock()  # lock to only instantiate one component at a time

    def __init__(self, settings: Settings):
        self._logger = Logger()
        self._settings = settings
        self._unload_in_progress = False  # don't generate new objects
        self._components: Dict[str, Component] = {}  # holds all the instances
        self._sensors: Dict[str, "SensorComponent"] = {}  # mapping from components to specific sensor types
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

    def get_sensors(self):
        return self._sensors

    def stop_component_instance(self, instance):
        """
        Stops a component based on an instance. 
        This is meant for a component to commit sudoku, e.g. when for restarting itself.
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
        sensors_to_delete = []
        for sensor in self._sensors:
            if instance is self._sensors[sensor]:
                sensors_to_delete.append(sensor)
        for sensor in sensors_to_delete:
            self._sensors.pop(sensor)

    def stop_component(self, name, reload_intended=False):
        """ Stops a component. CyclicComponentRegistry can take some time. """
        with self.comp_init_lock:
            component = self._components.get(name)
            if not component:
                return
            # don't do anything, when reload is intended and the component forbids it
            if reload_intended and component.reload_forbidden:
                return
            self._components.pop(name)
            self._logger.info("ComponentRegistry: Stopping %s", name)
            component.stop()
            # call destructors
            del component

    def watch_all(self):
        """ Check all components and thus initialize them """
        # filter for headless mode
        comps = [
            self.auto_updater, self.temp_sensor, self.humidity_sensor,
            self.tvoc_sensor, self.pressure_sensor, self.co2_sensor, self.motion_detection_sensor,
            self.server, self.weather_info]
        if not waqd.HEADLESS_MODE:
            comps += [self.event_handler, self.display, self.tts, self.sound, self.energy_saver]
        return comps

    @property
    def display(self) -> "Display":
        """ Access for Display singleton """
        from waqd.components import Display
        return self._create_component_instance(Display, [self._settings.get_string(DISPLAY_TYPE),
                                                         self._settings.get_int(BRIGHTNESS),
                                                         self._settings.get_int(WAVESHARE_DISP_BRIGHTNESS_PIN)])

    @property
    def event_handler(self) -> "EventHandler":
        """ Access for Greeter singleton """
        from waqd.components import EventHandler
        return self._create_component_instance(EventHandler, [self, self._settings.get(LANG),
                                                              self._settings.get(NIGHT_MODE_END),
                                                              self._settings.get(EVENTS_ENABLED)])

    @property
    def tts(self) -> "TextToSpeach":
        """ Access for TTS singleton """
        from waqd.components import TextToSpeach
        return self._create_component_instance(TextToSpeach, [self, self._settings.get(LANG)])

    @property
    def sound(self) -> "Sound":
        """ Access for Sound singleton """
        from waqd.components import Sound
        return self._create_component_instance(Sound, [self, self._settings.get(SOUND_ENABLED)])

    @property
    def energy_saver(self) -> "ESaver":
        """ Access for ESaver singleton """
        from waqd.components.power import ESaver
        return self._create_component_instance(ESaver, [self, self._settings])

    @property
    def weather_info(self) -> "OpenWeatherMap":
        """ Access for OnlineWeather singleton """
        from waqd.components.online_weather import OpenWeatherMap
        location = self._settings.get_string(LOCATION)
        return self._create_component_instance(OpenWeatherMap, [self._settings.get_dict(OW_CITY_IDS).get(location, ""),
                                                                self._settings.get(OW_API_KEY)])

    @property
    def auto_updater(self) -> "OnlineUpdater":
        """ Access for OnlineUpdater singleton """
        from waqd.components.updater import OnlineUpdater
        return self._create_component_instance(OnlineUpdater, [self, self._settings.get(AUTO_UPDATER_ENABLED),
                                                               self._settings.get(UPDATER_USER_BETA_CHANNEL)])

    @property
    def server(self) -> "Server":
        from waqd.components import Server
        return self._create_component_instance(Server, [self, 
                self._settings.get(SERVER_ENABLED), self._settings.get(USER_SESSION_SECRET), self._settings.get(USER_API_KEY)])

    @property
    def temp_sensor(self) -> "TempSensor":
        """ Access for temperature sensor  """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.TempSensor)
        if not sensor:
            dht22_pin = self._settings.get(DHT_22_PIN)
            if self._settings.get_string(REMOTE_MODE_URL):
                sensor = self._create_component_instance(sensors.WAQDRemoteStation, [self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self._create_component_instance(sensors.BME280, [self, self._settings])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self._create_component_instance(sensors.BMP280, [self, self._settings])
            elif dht22_pin != DHT_22_DISABLED:
                            sensor = self._create_component_instance(sensors.DHT22, [dht22_pin, self, self._settings])
            else:  # create a default instance that is disabled, so the watchdog
                # won't try to instantiate a new one over and over
                sensor = self._create_component_instance(sensors.TempSensor, [False, 1, False])
            self._sensors.update({sensors.TempSensor.__name__: sensor})
            sensor.select_for_temp_logging()
        return sensor

    @property
    def humidity_sensor(self) -> "HumiditySensor":
        """ Access for humidity sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.HumiditySensor)
        if not sensor:
            # DHT-22 is prioritized, if both are available
            dht22_pin = self._settings.get(DHT_22_PIN)
            if self._settings.get_string(REMOTE_MODE_URL):
                sensor = self._create_component_instance(sensors.WAQDRemoteStation, [self, self._settings])
            elif dht22_pin != DHT_22_DISABLED:
                sensor = self._create_component_instance(sensors.DHT22, [dht22_pin, self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self._create_component_instance(sensors.BME280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self._create_component_instance(
                    sensors.HumiditySensor, [False, 1, False])
            self._sensors.update({sensors.HumiditySensor.__name__: sensor})
            sensor.select_for_hum_logging()
        return sensor

    @property
    def pressure_sensor(self) -> "BarometricSensor":
        """ Access for pressure sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.BarometricSensor)
        if not sensor:
            if self._settings.get_string(REMOTE_MODE_URL):
                sensor = self._create_component_instance(sensors.WAQDRemoteStation, [self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self._create_component_instance(sensors.BME280, [self, self._settings])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self._create_component_instance(sensors.BMP280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self._create_component_instance(
                    sensors.BarometricSensor, [False, 1, False])
            self._sensors.update({sensors.BarometricSensor.__name__: sensor})
            sensor.select_for_pres_logging()
        return sensor

    @property
    def co2_sensor(self) -> "CO2Sensor":
        """ Access for air_quality_sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.CO2Sensor)
        if not sensor:
            # MH_Z19 is prioritized, if both are available
            if self._settings.get_string(REMOTE_MODE_URL):
                sensor = self._create_component_instance(sensors.WAQDRemoteStation, [self, self._settings])
            elif self._settings.get(MH_Z19_ENABLED):
                sensor = self._create_component_instance(sensors.MH_Z19, [self._settings])
            elif self._settings.get(CCS811_ENABLED):
                sensor = self._create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self._create_component_instance(sensors.CO2Sensor, [False, 1, False])
            self._sensors.update({sensors.CO2Sensor.__name__: sensor})
            sensor.select_for_co2_logging()
        return sensor

    @property
    def tvoc_sensor(self) -> "TvocSensor":
        """ Access for air_quality_sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.TvocSensor)
        if not sensor:
            if self._settings.get(CCS811_ENABLED):
                sensor = self._create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self._create_component_instance(sensors.TvocSensor, [False, 1, False])
            self._sensors.update({sensors.TvocSensor.__name__: sensor})
            sensor.select_for_tvoc_logging()
        return sensor

    @property
    def dust_sensor(self) -> "DustSensor":
        """ Access for dust sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.DustSensor)
        if not sensor:
            # if self._settings.get(GP2Y1010AU0F_ENABLED):
            #     sensor = self.create_component_instance(sensors.GP2Y1010AU0F, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self._create_component_instance(sensors.DustSensor, [False, 1, False])
            self._sensors.update({sensors.DustSensor.__name__: sensor})
            sensor.select_for_dust_logging()
        return sensor

    @property
    def light_sensor(self) -> "LightSensor":
        """ Access for light sensor """
        from waqd.components import sensors
        sensor = self._get_sensor(sensors.LightSensor)
        if not sensor:
            # if self._settings.get(CGY302_ENABLED):
            #     sensor = self.create_component_instance(sensors.GY302, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self._create_component_instance(sensors.LightSensor, [False, 1, False])
            self._sensors.update({sensors.LightSensor.__name__: sensor})
            sensor.select_for_light_logging()
        return sensor

    @property
    def motion_detection_sensor(self) -> "SR501":
        """ Access for motion_detection_sensor singleton """
        from waqd.components import sensors
        internal_name = "MotionSensor"
        sensor = self._get_sensor(sensors.SR501)
        if not sensor:
            pin = self._settings.get_int(MOTION_SENSOR_PIN)
            if self._settings.get(MOTION_SENSOR_ENABLED) and pin > 0:
                sensor = self._create_component_instance(sensors.SR501, [pin])
            else:  # create a default instance that is disabled
                sensor = self._create_component_instance(sensors.SR501, [0])
            self._sensors.update({sensors.SR501.__name__: sensor})
        return sensor

    @property
    def remote_exterior_sensor(self) -> "WAQDRemoteSensor":
        """ Access for remote_exterior_sensor singleton """
        from waqd.components.sensors import WAQDRemoteSensor

        sensor = self._get_sensor(WAQDRemoteSensor)
        if not sensor:
            sensor = self._create_component_instance(
                WAQDRemoteSensor, [self._settings, WAQDRemoteSensor.EXTERIOR_MODE])
            # TODO check features - diff ext and int
            sensor.select_for_hum_logging()
            sensor.select_for_temp_logging()
            self._sensors.update({WAQDRemoteSensor.__name__: sensor})
        return sensor

    @property
    def remote_interior_sensor(self) -> "WAQDRemoteSensor":
        """ Access for remote_interior_sensor singleton """
        from waqd.components.sensors import WAQDRemoteSensor

        sensor = self._get_sensor(WAQDRemoteSensor)
        if not sensor:
            sensor = self._create_component_instance(
                WAQDRemoteSensor, [self._settings, WAQDRemoteSensor.INTERIOR_MODE])
            sensor.select_for_hum_logging()
            sensor.select_for_temp_logging()
            self._sensors.update({WAQDRemoteSensor.__name__: sensor})
        return sensor

    S = TypeVar('S', bound="SensorComponent")  # can't import SensorComponent directly

    def _get_sensor(self, class_ref: Type[S]) -> Optional[S]:
        name = class_ref.__name__
        sensor = self._sensors.get(name)
        if sensor:
            if not isinstance(sensor, class_ref):
                raise TypeError(f"FATAL: Component {str(sensor)}has unexpected type.")
        return sensor

    T = TypeVar('T', bound=Component)

    def _create_component_instance(self, class_ref: Type[T], args: List = [], name_ref=None) -> T:
        """ Generic method for component creation and access. """
        name = class_ref.__name__
        if name_ref:
            name = name_ref
        with self.comp_init_lock:
            component = self._components.get(name)
            if component:
                if not isinstance(component, class_ref):
                    raise TypeError(f"FATAL: Component {str(component)}has unexpected type.")
                return component

            if self._unload_in_progress:
                pass
                # time.sleep(100) TODO: do here something meaningful...
            if issubclass(class_ref, Component):
                component = class_ref(*args)
                self._components.update({name: component})
            else:
                raise TypeError("The component " + str(class_ref) +
                                " to be created must be subclass of 'Component', but is instead a " +
                                class_ref.__class__.__name__ + " .")
            return component
