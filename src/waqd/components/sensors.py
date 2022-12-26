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
"""
This module contains all high abstraction classes of sensors, which internally
periodically call get a value (or use callbacks).
"""

import datetime
import os
import sys
import threading
import time

from ast import literal_eval
from statistics import mean
from subprocess import check_output
import requests
from typing import Optional, TYPE_CHECKING

from pint import Quantity
from waqd import LOCAL_TIMEZONE
from waqd.app import unit_reg
from waqd.base.component import Component, CyclicComponent
from waqd.base.component_reg import ComponentRegistry
from waqd.base.file_logger import Logger, SensorFileLogger
from waqd.base.db_logger import InfluxSensorLogger
from waqd.base.network import Network
from waqd.settings import (LAST_ALTITUDE_M_VALUE, LAST_TEMP_C_OUTSIDE_VALUE,
                           LOG_SENSOR_DATA, MH_Z19_VALUE_OFFSET, REMOTE_MODE_URL, USER_API_KEY, Settings)

if TYPE_CHECKING:
    from waqd.components.server import SensorApi_0_1
    import adafruit_bmp280
    from adafruit_bme280.advanced import Adafruit_BME280_I2C
    import adafruit_ccs811
    import adafruit_bh1750

SENSOR_INTERIOR_TYPE = "interior"
SENSOR_EXTERIOR_TYPE = "exterior"
DEFAULT_MAX_MEASURE_POINTS = 5
DEFAULT_INVALIDATION_TIME_S = 60


class SensorComponent(Component):
    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self._readings_stabilized = False

    @property
    def readings_stabilized(self) -> bool:
        """ Returns true, if sensor is warmed up and readings are considered valid. """
        return self._readings_stabilized

    @property
    def is_disabled(self) -> bool:
        return self._disabled

    def get_value_with_status(self, impl: "SensorImpl"):
        if self._disabled:
            return None
        value = impl.get_value()
        if value is None:
            self._disabled = True
        self._disabled = False
        return value


class SensorImpl():
    """ Class for any sensor type to store measurements with a moving average.
        Logs to file/db, if "log_to_file" is activated.
        To be used with pimpl pattern and not as a base class!
    """
    LOGGING_INTERVAL = datetime.timedelta(minutes=1)
    MAX_TIMES_DELTA_VIOLATED = 1

    def __init__(self, logging_enabled: bool, log_location_type: str, log_measure_type: str,
                 min_value: float, max_value: float, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, 
                 default_value=0, invalidation_time_s=30, max_delta=0, rounding_precision=2, rounding_base=1.0):
        # logging
        self.log_values = False # Select this instance for global for logging 
        # only check at init - options will reset this flag, with the exception of non-resettable sensors
        self._logging_enabled = logging_enabled
        self._log_measure_type = log_measure_type  # like temp or hum
        self._log_location_type = log_location_type  # like interior or exterior
        # value validation and rounding
        self._rounding_base = rounding_base
        self._rounding_prec = rounding_precision
        self._min_value = min_value  # for validation: outside this range invalid
        self._max_value = max_value  # same as min_value
        # maximum deviation for previous value - to detect errors (0 means disabled)
        self._max_delta = max_delta
        self._n_delta_violation = 0  # track violations - after MAX_TIMES_DELTA_VIOLATED times still take it
        self._first_value_written = False
        # value storage
        self._values_capacity = max_measure_points  # number of elements of the moving average
        self._values = []
        # After invalidation_time_s has passed, the sensor value will be considered out of date and return None for value
        # Does not make sense for motion sensors and such.
        self._last_value_rcv_time = datetime.datetime.now()
        self._value_invalidation_time_s = invalidation_time_s
        self._last_logging_time = datetime.datetime.now()

        # even if logging is disabled now we should attempt to restore the last recorded value
        # TODO does not work because of time limit - need find last value
        # use file logger when shuttings down and read back here
        if logging_enabled:
            # only enabled sensor returns values 
            log_values = InfluxSensorLogger.get_sensor_values(self._log_location_type, self._log_measure_type)
            if log_values:
                if len(log_values[0]) < 2:
                    Logger().warning(
                        f"Cant initialize {log_measure_type} sensor from log. Invalid log format.")
                else:
                    try:
                        last_date = log_values[0][0]
                    except:
                        return
                    if (last_date - datetime.datetime.now(LOCAL_TIMEZONE)) < datetime.timedelta(hours=3):
                        self._values.append(log_values[0][1])
            else:
                self._values.append(default_value)
        else:
            self._values.append(default_value)


    def stop(self):
        # save value to reread, when initializing
        SensorFileLogger.set_value(self._log_location_type, self._log_measure_type, self.get_value())

    def get_value(self) -> Optional[float]:
        """ Return measurement value. """
        # invalidation guard
        if datetime.datetime.now() - self._last_value_rcv_time > datetime.timedelta(seconds=self._value_invalidation_time_s):
            Logger().debug(f"Invalidated value of {self.__class__.__name__} {self._log_measure_type}")
            return None
        if self._values_capacity == 1:
            return self._values[0]
        else:
            return mean(self._values)

    @staticmethod
    def round(value: float, prec=2, base=.05):
        return round(base * round(value/base), prec)

    def set_value(self, value: Optional[float]) -> bool:
        """ Generic method to write values into the measurement list and manage its length """
        # out of bounds check
        Logger().debug("%s: %s Attempting to write %f",
                        self.__class__.__name__, self._log_measure_type, value)
        if value is None:
            return False
        value = self.round(value, self._rounding_prec, self._rounding_base)
        if not self._min_value <= value <= self._max_value:
            Logger().warning("%s: %s out of bounds %s", self.__class__.__name__,
                             self._log_measure_type, value)
            return False
        # max delta check - only check after first value has truly been written

        if self._max_delta and self._first_value_written:
            if current_value := self._values[-1]:
                current_delta = abs(value - current_value)
                if  current_delta >= self._max_delta:
                    if self._n_delta_violation < self.MAX_TIMES_DELTA_VIOLATED:
                        self._n_delta_violation += 1
                        Logger().warning("%s: %s max delta reached %s", self.__class__.__name__,
                                         self._log_measure_type, current_delta)
                        return False
                    else:
                        Logger().warning("%s: %s taking value after max delta reached.",
                                self.__class__.__name__, self._log_measure_type)
                        self._n_delta_violation = 0
        self._values.append(value)
        self._last_value_rcv_time = datetime.datetime.now()
        self._first_value_written = True

        if len(self._values) > self._values_capacity:
            self._values.pop(0)
        # log only at full measurement window - slower logging
        if self._logging_enabled and self.log_values:
            if datetime.datetime.now() - self._last_logging_time <= self.LOGGING_INTERVAL:
                return True
            # log the mean average of the values
            InfluxSensorLogger().set_value(self._log_location_type, self._log_measure_type, self.get_value())
            self._last_logging_time = datetime.datetime.now()
        return True


class TempSensor(SensorComponent):
    """ Base class for all temperature sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True,  # TODO add consts for "temp_degC"
                 log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="temp_degC",
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        """ is_disabled is for the case, when no sensor can be instantiated """
        SensorComponent.__init__(self, enabled=enabled)
        min_value = -30
        max_value = 60
        self._temp_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                     max_measure_points, 22, invalidation_time_s, 3)
        self.get_temperature()  # init unit registry

    def select_for_temp_logging(self):
        self._temp_impl.log_values = True

    def get_temperature(self) -> Optional[Quantity]:
        """ Return temperature in degree Celsius """
        value = self.get_value_with_status(self._temp_impl)
        if value:
            return Quantity(value, unit_reg.degC)
        else:
            return None

    def _set_temperature(self, value: Optional[float]) -> bool:
        return self._temp_impl.set_value(value)

    def stop(self):
        self._temp_impl.stop()


class BarometricSensor(SensorComponent):
    """ Base class for all barometric sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True, 
                 log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="pressure_hPa", 
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 800
        max_value = 2000
        self._pres_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                     max_measure_points, 1000, invalidation_time_s,
                                     max_delta=5, rounding_precision=0)

    def select_for_pres_logging(self):
        self._pres_impl.log_values = True

    def get_pressure(self) -> Optional[float]:
        """ Return the pressure in hPa """
        return self.get_value_with_status(self._pres_impl)

    def _set_pressure(self, value: Optional[float]):
        self._pres_impl.set_value(value)

    def _convert_abs_pres_to_asl(self, pressure: float, height_asl: float, temp_outdoor: float):
        """ Converts raw absolute readings to above sea level relative readings, which are used in weather forecasts. """
        return pressure * pow(1 - (0.0065 * height_asl / (temp_outdoor + (0.0065 * height_asl) + 273.15)), -5.257)

    def stop(self):
        self._pres_impl.stop()


class HumiditySensor(SensorComponent):
    """ Base class for all humidity sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True,
                log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="humidity_%",
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 10
        max_value = 100

        self._hum_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                    max_measure_points, 50, invalidation_time_s,
                                    max_delta=10, rounding_precision=0)

    def select_for_hum_logging(self):
        self._hum_impl.log_values = True

    def get_humidity(self) -> Optional[float]:
        """ Return the humidity in % """
        return self.get_value_with_status(self._hum_impl)

    def _set_humidity(self, value: Optional[float]):
        self._hum_impl.set_value(value)

    def stop(self):
        self._hum_impl.stop()


class TvocSensor(SensorComponent):
    """ Base class for all TVOC sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True,
                log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="TVOC",
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 0
        max_value = 500
        self._tvoc_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value,
                                     max_value, max_measure_points, 0, invalidation_time_s,
                                     max_delta=100, rounding_precision=0, rounding_base=5)

    def select_for_tvoc_logging(self):
        self._tvoc_impl.log_values = True

    def get_tvoc(self) -> Optional[float]:
        """ Returns TVOC in ppb """
        return self.get_value_with_status(self._tvoc_impl)

    def _set_tvoc(self, value: Optional[float]):
        self._tvoc_impl.set_value(value)

    def stop(self):
        self._tvoc_impl.stop()


class CO2Sensor(SensorComponent):
    """ Base class for all CO2 sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True, 
                 log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="CO2_ppm",
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 400
        max_value = 5000
        self._co2_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                    max_measure_points, 450, invalidation_time_s,
                                    max_delta=50, rounding_precision=0, rounding_base=5)

    def select_for_co2_logging(self):
        self._co2_impl.log_values = True

    def get_co2(self) -> Optional[float]:
        """ Returns equivalent CO2 in ppm """
        return self.get_value_with_status(self._co2_impl)

    def _set_co2(self, value: Optional[float]):
        self._co2_impl.set_value(value)

    def stop(self):
        self._co2_impl.stop()


class DustSensor(SensorComponent):
    """ Base class for all dust sensors """

    def __init__(self, logging_enabled: bool, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True,
                 log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="dust_ug_per_m3",
                 invalidation_time_s=DEFAULT_INVALIDATION_TIME_S):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 0
        max_value = 1000
        self._dust_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                     max_measure_points, 100, invalidation_time_s, 
                                     max_delta=100, rounding_precision=0)

    def select_for_dust_logging(self):
        self._dust_impl.log_values = True

    def get_dust(self) -> Optional[float]:
        """ Returns dust in ug/m^3 """
        return self.get_value_with_status(self._dust_impl)

    def _set_dust(self, value: Optional[float]):
        self._dust_impl.set_value(value)

    def stop(self):
        self._dust_impl.stop()


class LightSensor(SensorComponent):
    """ Base class for all light sensors """

    def __init__(self, logging_enabled, max_measure_points=DEFAULT_MAX_MEASURE_POINTS, enabled=True, 
                log_location_type=SENSOR_INTERIOR_TYPE, log_measure_type="light_lux", invalidation_time_s=15):
        SensorComponent.__init__(self, enabled=enabled)
        min_value = 0  # dark
        max_value = 100000  # direct sunlight
        self._light_impl = SensorImpl(logging_enabled, log_location_type, log_measure_type, min_value, max_value,
                                      max_measure_points, 10000, invalidation_time_s,
                                      max_delta=0, rounding_precision=0) # max_delta is practically infinite

    def select_for_light_logging(self):
        self._light_impl.log_values = True

    def get_light(self) -> Optional[float]:
        """ Returns light in lux """
        return self.get_value_with_status(self._light_impl)

    def _set_light(self, value: Optional[float]):
        self._light_impl.set_value(value)

    def stop(self):
        self._light_impl.stop()


class DHT22(TempSensor, HumiditySensor, CyclicComponent):
    """
    Implements access to the DHT22 temperature/humidity sensor.
    """
    UPDATE_TIME = 5  # in seconds
    MEASURE_POINTS = 2

    def __init__(self, pin: int, components: ComponentRegistry, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        TempSensor.__init__(self, log_values, self.MEASURE_POINTS)
        HumiditySensor.__init__(self, log_values, self.MEASURE_POINTS)
        CyclicComponent.__init__(self, components, enabled=bool(pin))
        self._comps: ComponentRegistry
        self._pin = pin
        self._sensor_driver = None
        self._error_num = 0
        if self._disabled:
            self._logger.error("DHT22: No pin, disabled")
            return
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        from adafruit_dht import \
            DHT22 as DHT22_drv  # pylint: disable=import-outside-toplevel
        # driver uses pulseio - only one process can be open
        self._kill_libgpiod()
        self._sensor_driver = DHT22_drv(self._pin)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        humidity = 0
        temperature = 0
        if not self._sensor_driver:
            self._disabled = True
            return
        try:
            humidity = self._sensor_driver.humidity
            temperature = self._sensor_driver.temperature
        except Exception as error:
            self._error_num += 1
            # errors happen fairly often, keep going
            self._logger.error("DHT22: Can't read sensor - %s", str(error))
            return
        if self._error_num >= 3:
            self._logger.error("DHT22: Restarting sensor after 3 errors")
            self._comps.stop_component_instance(self)
            return
        self._error_num = 0

        self._set_humidity(humidity)
        valid = self._set_temperature(temperature)
        if not valid:
            self._error_num += 1

        self._logger.debug("DHT22: Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(
            temperature, humidity))

    def stop(self):  # override Component
        super().stop()
        if self._sensor_driver:
            self._sensor_driver.exit()
            del self._sensor_driver
            self._kill_libgpiod()

    def _kill_libgpiod(self):
        if not self._runtime_system.is_target_system:  # don't check on non target system
            return
        try:
            pids = check_output(["pgrep", "libgpiod_pulsei"]).decode("utf-8")
            for pid in pids.split("\n"):
                os.system("kill " + str(pid))
        except Exception as error:  # works on RPi3 pulsi does not
            self._logger.warning("DHT22: Exception while checking running pulseio process: %s", str(error))


class BMP280(TempSensor, BarometricSensor, CyclicComponent):
    """
    Implements access to the BMP280 temperature/pressure sensor.
    """
    UPDATE_TIME = 5  # in seconds
    MEASURE_POINTS = 2

    def __init__(self, components: ComponentRegistry, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        self._comps: ComponentRegistry
        TempSensor.__init__(self, log_values, self.MEASURE_POINTS)
        BarometricSensor.__init__(self, log_values, self.MEASURE_POINTS)
        CyclicComponent.__init__(self, components, settings)

        self._sensor_driver: "adafruit_bmp280.Adafruit_BMP280_I2C"
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        # use the old Adafruit driver, the new one is more unstable
        import adafruit_bmp280
        import board  # pylint: disable=import-outside-toplevel
        i2c = board.I2C()   # uses board.SCL and board.SDA
        self._sensor_driver = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        temperature = 0
        pressure = 0
        try:
            temperature = self._sensor_driver.temperature
            pressure = self._sensor_driver.pressure
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("BMP280: Can't read sensor - %s", str(error))
            return
        altitude = self._settings.get_float(LAST_ALTITUDE_M_VALUE)
        temp_outside = self._settings.get_float(LAST_TEMP_C_OUTSIDE_VALUE)
        weather = self._comps.weather_info.get_current_weather()
        if weather:
            altitude = weather.altitude
            temp_outside = weather.temp

        self._set_pressure(self._convert_abs_pres_to_asl(pressure, altitude, temp_outside))
        self._set_temperature(temperature)

        self._logger.debug("BMP280: Temp={0:0.1f}*C  Pressure={1}hPa".format(
            temperature, pressure))


class BME280(TempSensor, BarometricSensor, HumiditySensor, CyclicComponent):
    """
    Implements access to the BME280 temperature/humidity/pressure sensor.
    """
    UPDATE_TIME = 5  # in seconds
    MEASURE_POINTS = 5

    def __init__(self, components: ComponentRegistry, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        self._comps: ComponentRegistry
        TempSensor.__init__(self, log_values, self.MEASURE_POINTS)
        BarometricSensor.__init__(self, log_values, self.MEASURE_POINTS)
        HumiditySensor.__init__(self, log_values, self.MEASURE_POINTS)
        CyclicComponent.__init__(self, components, settings)

        self._sensor_driver: "Adafruit_BME280_I2C"
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        from adafruit_bme280.advanced import Adafruit_BME280_I2C
        import board  # pylint: disable=import-outside-toplevel
        i2c = board.I2C()   # uses board.SCL and board.SDA
        self._sensor_driver = Adafruit_BME280_I2C(i2c, address=0x76)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        temperature = 0
        pressure = 0
        humidity = 0
        try:
            temperature = self._sensor_driver.temperature
            pressure = self._sensor_driver.pressure
            humidity = self._sensor_driver.humidity
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("BME280: Can't read sensor - %s", str(error))
            return

        # change this to match the location's pressure (hPa) at sea level
        altitude = self._settings.get_float(LAST_ALTITUDE_M_VALUE)
        temp_outside = self._settings.get_float(LAST_TEMP_C_OUTSIDE_VALUE)
        if Network().internet_connected:
            weather = self._comps.weather_info.get_current_weather()
            if weather:
                altitude = weather.altitude
                temp_outside = weather.temp

        self._set_pressure(self._convert_abs_pres_to_asl(pressure, altitude, temp_outside))
        self._set_temperature(temperature)
        self._set_humidity(humidity)

        self._logger.debug("BME280: Temp={0:0.1f}*C  Pressure={1}hPa Humidity={2:0.1f}%".format(
            temperature, pressure, humidity))


class MH_Z19(CO2Sensor, CyclicComponent):  # pylint: disable=invalid-name
    """
    Implements access to the MH-Z19 CO2 sensor.
    Return the values as a moving average of the last points.
    Does not measure temperature, because it is very imprecise.
    """
    UPDATE_TIME = 3  # in seconds
    MEASURE_POINTS = 5
    STABILIZE_TIME_MINUTES = 3  # in minutes

    def __init__(self, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        CO2Sensor.__init__(self, log_values, self.MEASURE_POINTS)
        CyclicComponent.__init__(self)
        self._offset = settings.get_int(MH_Z19_VALUE_OFFSET)
        self._start_time = datetime.datetime.now()
        self._readings_stabilized = False
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        # Switched to sudo + cli of the python module, because I found no reliable way
        # to automate the permission settings for the serial interface,
        # because of a bug? it resets after calling the python serial module.
        if self._runtime_system.is_target_system:
            os.system(f"sudo {sys.executable} -m mh_z19 --detection_range_2000")
            # disable auto calibration -> it will never read true 400ppm...
            os.system(f"sudo {sys.executable} -m mh_z19 --abc_off")

    def _read_sensor(self):
        co2 = 0
        output = ""
        try:
            # Parse back from cli
            if self._runtime_system.is_target_system:
                cmd = ["sudo", sys.executable, "-m", "mh_z19"]
            else:  # for local tests
                cmd = [sys.executable, "-m", "mh_z19"]
            output = check_output(cmd).decode("utf-8")
            output.strip()
            if not output or not "co2" in output.lower():
                self._logger.error("MH-Z19: Can't read sensor")
                return
            co2 = int(literal_eval(output).get("co2", ""))
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error(f"MH-Z19: Can't read sensor - {str(error)} Output: {output}",)
            return

        self._set_co2(co2 + self._offset)

        # eval stabilizer time
        stab_time = datetime.timedelta(minutes=self.STABILIZE_TIME_MINUTES)
        if datetime.datetime.now() > self._start_time + stab_time:
            self._readings_stabilized = True

        # log if value is readable
        self._logger.debug(
            'MH-Z19: CO2={0:0.1f}ppm'.format(co2))

    def zero_calibraton(self):
        os.system(f"sudo {sys.executable} -m mh_z19 --zero_point_calibration")


class CCS811(CO2Sensor, TvocSensor, CyclicComponent):  # pylint: disable=invalid-name
    """
    Implements access to the CCS811 CO2/TVOC sensor.
    Return the values as a moving average of the last points.
    """
    UPDATE_TIME = 3  # in seconds
    STABILIZE_TIME_MINUTES = 30  # minutes
    MEASURE_POINTS = 3

    def __init__(self, components: ComponentRegistry, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        CO2Sensor.__init__(self, log_values, self.MEASURE_POINTS)
        TvocSensor.__init__(self, log_values, self.MEASURE_POINTS)
        CyclicComponent.__init__(self, components)
        self._comps: ComponentRegistry

        self._start_time = datetime.datetime.now()
        self._reload_forbidden = True
        self._sensor_driver: "adafruit_ccs811.CCS811"
        self._error_num = 0

        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Inits driver and tries to communicate.
        Imports the real driver only on target platform.
        """
        import adafruit_ccs811
        import board
        import busio  # pylint: disable=import-outside-toplevel
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._sensor_driver = adafruit_ccs811.CCS811(i2c)

            # wait for the sensor to be ready - try max 3 times
            i = 0
            while not self._sensor_driver.data_ready and i <= 3:
                i += 1
                time.sleep(1)
        except Exception as error:
            self._logger.error("CCS811: can not be initialized - %s", str(error))
            return

    def _react_on_error(self):
        if self._error_num == 2:
            self._logger.error("CCS811: Error in reading sensor. Resetting ...")
            if self._sensor_driver:
                try:
                    self._sensor_driver.reset()
                except Exception as error:
                    self._logger.error("CCS811: can not be resetted - %s", str(error))
                    self._disabled = True
            else:  # driver failed to start (wiring issues?)
                self._disabled = True
        if self._error_num == 3:
            self._logger.error("CCS811: Error in reading sensor. Restarting...")
            del self._sensor_driver
            self._init_sensor()

    def _set_environmental_values(self):
        """
        If there is a temperature/humidity sensor, it can be
        used to initalize this sensor, so it has more accurate measurements
        """
        temperature = self._comps.temp_sensor.get_temperature()
        humidity = self._comps.humidity_sensor.get_humidity()
        # wait for values to stabilize
        if temperature is None or humidity is None:
            return
        while not 15 < temperature < 50:
            time.sleep(2)

        self._sensor_driver.set_environmental_data(int(humidity), float(temperature))

    def _read_sensor(self):
        """
        Cyclic function for reading the actual values into a moving average list.
        Sets environment values from an optional temp/hum sensor.
        Does a soft restart after 2 errors and a hard reset after 3 errors.
        """
        co2 = None
        tvoc = None
        try:
            self._react_on_error()
            if self._sensor_driver.data_ready:
                co2 = self._sensor_driver.eco2
                tvoc = self._sensor_driver.tvoc
                # eval stabilizer time
                stab_time = datetime.timedelta(minutes=self.STABILIZE_TIME_MINUTES)
                if datetime.datetime.now() > self._start_time + stab_time:
                    self._readings_stabilized = True

            else:
                self._error_num += 1
                return

            self._error_num = 0
        except Exception as error:  # there are a miriad of errors...
            self._error_num += 1
            self._logger.error("CCS811: Error in reading sensor - %s", str(error))
            return

        self._set_co2(co2)
        self._set_tvoc(tvoc)

        # log if every value is readable
        self._logger.debug('CCS811: CO2={0:0.1f}ppm TVOC={1:0.1f}'.format(co2, tvoc))


class BH1750(LightSensor, CyclicComponent):
    """
    Implements access to the BH1750 light intensity sensor.
    WARNING: PROTOTYPE STATUS!
    """
    UPDATE_TIME = 1  # in seconds

    def __init__(self, settings: Settings):
        MEASURE_POINTS = 2
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        LightSensor.__init__(self, log_values, MEASURE_POINTS)
        CyclicComponent.__init__(self)

        self._sensor_driver: "adafruit_bh1750.BH1750"
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        import adafruit_bh1750
        import board
        i2c = board.I2C()
        self._sensor_driver = adafruit_bh1750.BH1750(i2c)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        light = 0
        try:
            self._sensor_driver.lux
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("GY302: Can't read sensor - %s", str(error))
            return
        self._set_light(light)
        self._logger.debug("GY302: Light={0:0.1f}Lux".format(light))


class GP2Y1010AU0F(DustSensor, CyclicComponent):
    """
    Implements access to the GP2Y1010AU0F dust density sensor.
    WARNING: PROTOTYPE STATUS!
    """
    UPDATE_TIME = 1  # in seconds
    LED_PIN = 17  # BCM - TODO make setting

    def __init__(self, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        DustSensor.__init__(self, log_values)
        CyclicComponent.__init__(self, None, settings)
        self._gpio: "RPi.GPIO"  # type: ignore
        self._sensor_driver = None
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        import adafruit_ads1x15.ads1115 as ADS
        import board  # pylint: disable=import-outside-toplevel
        from adafruit_ads1x15.analog_in import AnalogIn
        import RPi.GPIO as GPIO  # type: ignore

        self._gpio = GPIO
        self._gpio.setup(self.LED_PIN, self._gpio.OUT)
        i2c = board.I2C()   # uses board.SCL and board.SDA
        # Create the ADC object using the I2C bus
        ads = ADS.ADS1115(i2c)
        # Create single-ended input on channels
        self._sensor_driver = AnalogIn(ads, ADS.P0)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        dust_ug_m3 = 0
        try:
            # TODO: Can Python even do such precise timing?
            self._gpio.output(self.LED_PIN, False)  # type: ignore
            time.sleep(0.000280)
            dust = self._sensor_driver.voltage  # type: ignore
            time.sleep(0.000040)
            self._gpio.output(self.LED_PIN, True)  # type: ignore
            time.sleep(0.009680)

        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("GP2Y1010AU0F: Can't read sensor - %s", str(error))
            return

        dust_ug_m3 = ((dust * 0.172) - 0.0999) * 1000  # from datasheet V->mg/m3
        self._set_dust(dust_ug_m3)

        self._logger.debug(f"GP2Y1010AU0F: Dust={dust_ug_m3}ug/m3")


class SR501(SensorComponent):  # pylint: disable=invalid-name
    """ Implements access to the SR501 infrared movement sensor. """
    BOUNCE_TIME = 3

    def __init__(self, pin):
        super().__init__()
        self._pin = pin
        self._motion_detected = 0
        self._sensor_driver: "RPi.GPIO"  # type: ignore
        if pin == 0:
            self._disabled = True
            return
        self._init_thread = threading.Thread(name="SR501_Init",
                                             target=self._register_callback,
                                             daemon=True)
        self._init_thread.start()

    def __del__(self):
        """ Cleanup GPIO """
        if self._disabled:
            return
        self._sensor_driver.setmode(self._sensor_driver.BCM)
        self._sensor_driver.remove_event_detect(self._pin)
        self._sensor_driver.cleanup()

    @property
    def motion_detected(self) -> bool:
        """ Returns true, if often motion was detected in the last 3 seconds. """
        return bool(self._motion_detected)

    def _register_callback(self):
        """ Initializer function, register the wake-up function to the configured pin."""
        try:
            import RPi.GPIO as GPIO  # type: ignore
            self._sensor_driver = GPIO
            self._sensor_driver.cleanup()
            self._sensor_driver.setmode(self._sensor_driver.BCM)
            self._sensor_driver.setup(self._pin, self._sensor_driver.IN)
            self._sensor_driver.add_event_detect(self._pin, self._sensor_driver.RISING,
                                                 callback=self._wake_up_from_sensor,
                                                 bouncetime=self.BOUNCE_TIME * 1000)
        except Exception as error:
            self._disabled = True
            self._logger.error("MotionDetector: sensor cannot be initialized: %s", str(error))

    def _wake_up_from_sensor(self, callback):  # pylint: disable=unused-argument
        """
        Callback function, when pin is high.
        Counting up and waiting is used to smooth out detection.
        """
        self._motion_detected += 1
        self._logger.debug("MotionDetector: motion detected %i", self._motion_detected)
        time.sleep(self.BOUNCE_TIME)
        self._motion_detected -= 1


class WAQDRemoteSensor(TempSensor, HumiditySensor):
    """ Remote sensor via WAQD HTTP service """

    MEASURE_POINTS = 3
    EXTERIOR_MODE = 0
    INTERIOR_MODE = 1


    def __init__(self, settings: Settings, mode=EXTERIOR_MODE):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        TempSensor.__init__(self, log_values, self.MEASURE_POINTS,
                            log_location_type=SENSOR_EXTERIOR_TYPE, invalidation_time_s=60)
        HumiditySensor.__init__(self, log_values, self.MEASURE_POINTS,
                                log_location_type=SENSOR_EXTERIOR_TYPE, invalidation_time_s=60)
        self._disabled = True  # don't know if connected at startup

    def read_callback(self, temperature, humidity):
        """
        """
        self._disabled = False

        self._set_temperature(temperature)
        self._set_humidity(humidity)
        self._logger.debug("WAQDExtTempSensor: Temp={0:0.1f}*C Humidity={1:0.1f}%".format(
            temperature, humidity))


class WAQDRemoteStation(TempSensor, HumiditySensor, BarometricSensor, CO2Sensor, CyclicComponent):
    MEASURE_POINTS = 1
    INIT_WAIT_TIME = 2
    UPDATE_TIME = 10

    def __init__(self, components: ComponentRegistry, settings: Settings):
        log_values = bool(settings.get(LOG_SENSOR_DATA))
        TempSensor.__init__(self, log_values, self.MEASURE_POINTS,
                            log_location_type=SENSOR_INTERIOR_TYPE, invalidation_time_s=self.UPDATE_TIME*6)
        HumiditySensor.__init__(self, log_values, self.MEASURE_POINTS,
                                log_location_type=SENSOR_INTERIOR_TYPE, invalidation_time_s=self.UPDATE_TIME*6)
        BarometricSensor.__init__(self, log_values, self.MEASURE_POINTS,
                                  log_location_type=SENSOR_INTERIOR_TYPE, invalidation_time_s=self.UPDATE_TIME*6)
        CO2Sensor.__init__(self, log_values, self.MEASURE_POINTS,
                           log_location_type=SENSOR_INTERIOR_TYPE, invalidation_time_s=self.UPDATE_TIME*6)
        CyclicComponent.__init__(self, components, settings, log_values)
        self._start_update_loop(self._read_sensor, self._read_sensor)
        self._url = settings.get_string(REMOTE_MODE_URL)
        self._readings_stabilized = True  # init with stabilized values, we know nothing about it

    def _read_sensor(self):
        Network().wait_for_network()
        try:
            response = requests.get(self._url + "/api/remoteIntSensor?APPID=" +
                                    self._settings.get_string(USER_API_KEY), timeout=5)  # "http://"
        except Exception as e:
            Logger().warning(f"Cannot reach {self._url}")
            return
        if not response.ok:
            Logger().warning(f"Cannot reach {self._url}")
            return()
        content: "SensorApi_0_1" = response.json()
        if (val := content.get("temp", "N/A")) not in ["None", "N/A"]:
            self._set_temperature(float(val))
        if (val := content.get("hum", "N/A")) not in ["None", "N/A"]:
            self._set_humidity(float(val))
        if (val := content.get("baro", "N/A")) not in ["None", "N/A"]:
            self._set_pressure(float(val))
        if (val := content.get("co2", "N/A")) not in ["None", "N/A"]:
            self._set_co2(float(val))
