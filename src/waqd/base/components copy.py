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
from typing import Dict, List, Optional, Type, Union, TYPE_CHECKING

from waqd.base.logger import Logger
from waqd.base.component import Component, CyclicComponent
from waqd.settings import (AUTO_UPDATER_ENABLED, BME_280_ENABLED, BMP_280_ENABLED, BRIGHTNESS,
                           CCS811_ENABLED, DHT_22_DISABLED, DHT_22_PIN, LANG,
                           DISPLAY_TYPE, MH_Z19_ENABLED, MOTION_SENSOR_ENABLED,
                           MOTION_SENSOR_PIN, SOUND_ENABLED, UPDATER_USER_BETA_CHANNEL,
                           WAVESHARE_DISP_BRIGHTNESS_PIN, Settings)

if TYPE_CHECKING:
    from waqd.components import (Display, ESaver, EventHandler, TextToSpeach, Sound, OpenWeatherMap, SR501,
                                 OnlineUpdater, TempSensor, TvocSensor, BarometricSensor, HumiditySensor,
                                 CO2Sensor, DustSensor, LightSensor, Prologue433)


class ComponentRegistry():
    """
    Abstraction to hold all components, create, stop and get access to them.
    An instance is passed automatically to all components.
    """
    # Constants for Component names to an alternitave method to access components

    comp_init_lock = threading.RLock()  # lock to only instantiate one component at a time

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
        from waqd.components import Display
        component = self.check_for_init_component(Display)
        if component and isinstance(component, Display):
            return component
        component = Display(self._settings.get_string(DISPLAY_TYPE), self._settings.get_int(BRIGHTNESS),
                self._settings.get_int(WAVESHARE_DISP_BRIGHTNESS_PIN))
        self._components.update({Display.__name__, component})
        return component

    @property
    def event_handler(self) -> "EventHandler":
        """ Access for Greeter singleton """
        from waqd.components import EventHandler
        component = self.check_for_init_component(EventHandler)
        if component and isinstance(component, EventHandler):
            return component
        return EventHandler(self, self._settings)

    @property
    def tts(self) -> "TextToSpeach":
        """ Access for TTS singleton """
        from waqd.components import TextToSpeach
        component = self.check_for_init_component(TextToSpeach)
        if component and isinstance(component, TextToSpeach):
            return component
        return TextToSpeach(self, self._settings.get(LANG))

    @property
    def sound(self) -> "Sound":
        """ Access for Sound singleton """
        from waqd.components.sound import Sound
        component = self.check_for_init_component(Sound)
        if component and isinstance(component, Sound):
            return component
        return Sound(self._settings.get(SOUND_ENABLED))

    @property
    def energy_saver(self) -> "ESaver":
        """ Access for ESaver singleton """
        from waqd.components.power import ESaver
        component = self.check_for_init_component(ESaver)
        if component and isinstance(component, ESaver):
            return component
        return ESaver(self, self._settings)

    @property
    def weather_info(self) -> "OpenWeatherMap":
        """ Access for OnlineWeather singleton """
        from waqd.components.online_weather import OpenWeatherMap
        component = self.check_for_init_component(OpenWeatherMap)
        if component and isinstance(component, OpenWeatherMap):
            return component
        return OpenWeatherMap(self._settings)

    @property
    def auto_updater(self) -> "OnlineUpdater":
        """ Access for OnlineUpdater singleton """
        from waqd.components.updater import OnlineUpdater
        component = self.check_for_init_component(OnlineUpdater)
        if component and isinstance(component, OnlineUpdater):
            return component
        return OnlineUpdater(self, self._settings.get(AUTO_UPDATER_ENABLED), 
                            self._settings.get(UPDATER_USER_BETA_CHANNEL))

    @property
    def temp_sensor(self) -> "TempSensor":
        """ Access for temperature sensor  """
        internal_name = "TempSensor"
        sensor: "TempSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors
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
            sensor.select_for_temp_logging()
        return sensor

    @property
    def humidity_sensor(self) -> "HumiditySensor":
        """ Access for humidity sensor """
        internal_name = "HumiditySensor"
        sensor: "HumiditySensor" = self._sensors.get(internal_name)
        if not sensor:
            # DHT-22 is prioritized, if both are available
            import waqd.components.sensors as sensors
            dht22_pin = self._settings.get(DHT_22_PIN)
            if dht22_pin != DHT_22_DISABLED:
                sensor = self.create_component_instance(sensors.DHT22, [dht22_pin, self, self._settings])
            elif self._settings.get(BME_280_ENABLED):
                sensor = self.create_component_instance(sensors.BME280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.HumiditySensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_hum_logging()
        return sensor

    @property
    def pressure_sensor(self) -> "BarometricSensor":
        """ Access for pressure sensor """
        internal_name = "BarometricSensor"
        sensor: "BarometricSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors
            if self._settings.get(BME_280_ENABLED):
                sensor = self.create_component_instance(sensors.BME280, [self, self._settings])
            elif self._settings.get(BMP_280_ENABLED):
                sensor = self.create_component_instance(sensors.BMP280, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.BarometricSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_pres_logging()
        return sensor

    @property
    def co2_sensor(self) -> "CO2Sensor":
        """ Access for air_quality_sensor """
        internal_name = "CO2Sensor"
        sensor: "CO2Sensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors

            # MH_Z19 is prioritized, if both are available
            if self._settings.get(MH_Z19_ENABLED):
                sensor = self.create_component_instance(sensors.MH_Z19, [self._settings])
            elif self._settings.get(CCS811_ENABLED):
                sensor = self.create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.CO2Sensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_co2_logging()
        return sensor

    @property
    def tvoc_sensor(self) -> "TvocSensor":
        """ Access for air_quality_sensor """
        internal_name = "TVOCSensor"
        sensor: "TvocSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors
            if self._settings.get(CCS811_ENABLED):
                sensor = self.create_component_instance(sensors.CCS811, [self, self._settings])
            else:  # create a default instance that is disabled
                sensor = self.create_component_instance(sensors.TvocSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_tvoc_logging()
        return sensor

    @property
    def dust_sensor(self) -> "DustSensor":
        """ Access for dust sensor """
        internal_name = "DustSensor"
        sensor: "DustSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors

            # if self._settings.get(GP2Y1010AU0F_ENABLED):
            #     sensor = self.create_component_instance(sensors.GP2Y1010AU0F, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self.create_component_instance(sensors.DustSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_dust_logging()
        return sensor

    @property
    def light_sensor(self) -> "LightSensor":
        """ Access for light sensor """
        internal_name = "LightSensor"
        sensor: "LightSensor" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors

            # if self._settings.get(CGY302_ENABLED):
            #     sensor = self.create_component_instance(sensors.GY302, [self, self._settings])
            # else:  # create a default instance that is disabled
            sensor = self.create_component_instance(sensors.LightSensor, [self._settings, True])
            self._sensors.update({internal_name: sensor})
            sensor.select_for_light_logging()
        return sensor

    @property
    def motion_detection_sensor(self) -> "SR501":
        """ Access for motion_detection_sensor singleton """
        internal_name = "MotionSensor"
        sensor: "SR501" = self._sensors.get(internal_name)
        if not sensor:
            import waqd.components.sensors as sensors
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
        from waqd.components.sensors import \
            Prologue433
        return self.create_component_instance(Prologue433, [self._settings])

    def check_for_init_component(self, class_ref: Type[Component]) -> Optional[Component]:
        internal_name = class_ref.__name__
        with self.comp_init_lock:
            component = self._components.get(internal_name)
            if component:
                return component
            if not self._unload_in_progress:
                self._logger.info("ComponentRegistry: Starting %s", class_ref.__name__)
                if not issubclass(class_ref, Component):
                    raise TypeError("The component " + str(class_ref) +
                                    " to be created must be subclass of 'Component', but is instead a " +
                                    class_ref.__class__.__name__ + " .")
                return None
