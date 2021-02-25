"""
This module contains all high abstraction classes of sensors, which internally
periodically call get a value (or use callbacks).
"""

import datetime
import threading
import time
import os
from statistics import mean
from subprocess import check_output
from typing import Optional
from piweather.base.components import (Component, ComponentRegistry,
                                       CyclicComponent)


class Sensor(Component):
    """ Base class for any sensor type to store measurements with a moving average """
    MEASURE_POINTS = 5

    def __init__(self, components=None, settings=None):
        super().__init__(components=components, settings=settings)
        self._readings_stabilized = False

    def set_value(self, value, meas_list, min_val, max_val, val_type):
        """ Generic method to write values into the measurement list and manage its length """
        if not min_val <= value <= max_val:
            self._logger.warning("%s: %s out of bounds %s", self.__class__.__name__,
                                 val_type, value)
            return
        if len(meas_list) == self.MEASURE_POINTS:
            meas_list.pop(0)
        meas_list.append(value)
        if len(meas_list) == 1:  # faster init
            meas_list.append(value)
            meas_list.append(value)

    @property
    def readings_stabilized(self) -> bool:
        """ Returns true, if sensor is warmed up and readings are considered valid. """
        return self._readings_stabilized


class TempSensor(Sensor):
    """ Base class for all temperature sensors """
    MIN_TEMP_VALUE = 0
    MAX_TEMP_VALUE = 50

    def __init__(self, is_disabled=False):
        """ is_disabled is for the case, when no sensor can be instanciated """
        super().__init__()
        self._temp_reading = [22]
        self._disabled = is_disabled

    def get_temperature(self) -> Optional[float]:
        """ Return temperature in degree Celsius """
        if self._disabled:
            return None
        return mean(self._temp_reading)

    def _set_temperature(self, value):
        self.set_value(value, self._temp_reading, self.MIN_TEMP_VALUE,
                       self.MAX_TEMP_VALUE, "temperature")


class BarometricSensor(Sensor):
    """ Base class for all barometric sensors """
    MIN_PRES_VALUE = 800
    MAX_PRES_VALUE = 2000

    def __init__(self, is_disabled=False):
        super().__init__()
        self._pres_reading = [1000]  # in hPa
        self._disabled = is_disabled

    def get_pressure(self) -> Optional[int]:
        """ Return the pressure in hPa """
        if self._disabled:
            return None
        return mean(self._pres_reading)

    def _set_pressure(self, value):
        self.set_value(value, self._pres_reading, self.MIN_PRES_VALUE,
                       self.MAX_PRES_VALUE, "pressure")


class HumiditySensor(Sensor):
    """ Base class for all humidity sensors """
    MIN_HUM_VALUE = 0
    MAX_HUM_VALUE = 100

    def __init__(self, is_disabled=False):
        super().__init__()
        self._hum_reading = [50]
        self._disabled = is_disabled

    def get_humidity(self) -> Optional[int]:
        """ Return the humidity in % """
        if self._disabled:
            return None
        return mean(self._hum_reading)

    def _set_humidity(self, value):
        self.set_value(value, self._hum_reading, self.MIN_HUM_VALUE,
                       self.MAX_HUM_VALUE, "humidity")


class TvocSensor(Sensor):
    """ Base class for all TVOC sensors """
    MIN_TVOC_VALUE = 0
    MAX_TVOC_VALUE = 500

    def __init__(self, is_disabled=False):
        super().__init__()
        self._tvoc_reading = [0]
        self._disabled = is_disabled

    def get_tvoc(self) -> Optional[float]:
        """ Returns TVOC in ppb """
        if self._disabled:
            return None
        return mean(self._tvoc_reading)

    def _set_tvoc(self, value):
        self.set_value(value, self._tvoc_reading, self.MIN_TVOC_VALUE,
                       self.MAX_TVOC_VALUE, "TVOC")


class CO2Sensor(Sensor, CyclicComponent):
    """ Base class for all CO2 sensors """
    MIN_CO2_VALUE = 400
    MAX_CO2_VALUE = 5000

    def __init__(self, is_disabled=False):
        super().__init__()
        self._co2_reading = [400]
        self._disabled = is_disabled

    def get_co2(self) -> Optional[float]:
        """ Returns equivalent CO2 in ppm """
        if self._disabled:
            return None
        return mean(self._co2_reading)

    def _set_co2(self, value):
        self.set_value(value, self._co2_reading, self.MIN_CO2_VALUE,
                       self.MAX_CO2_VALUE, "CO2")


class DHT22(TempSensor, HumiditySensor, CyclicComponent):
    """
    Implements access to the DHT22 temperature/humidity sensor.
    """
    UPDATE_TIME = 5  # in seconds
    MEASURE_POINTS = 5

    def __init__(self, pin, components: ComponentRegistry):
        TempSensor.__init__(self)
        HumiditySensor.__init__(self)
        CyclicComponent.__init__(self, components)
        self._pin = pin
        if not self._pin:
            self._logger.error("DHT22: No pin, disabled")
            self._disabled = True
            return
        self._sensor_driver = None
        self._error_num = 0
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        # use the old Adafruit driver, the new one is more unstable
        from adafruit_dht import DHT22  # pylint: disable=import-outside-toplevel
        self._sensor_driver = DHT22(self._pin)

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        humidity = 0
        temperature = 0
        try:
            humidity = self._sensor_driver.humidity
            temperature = self._sensor_driver.temperature
        except Exception as error:
            self._error_num += 1
            if self._error_num == 3:
                self._logger.error("DHT22: Restarting sensor after 3 errors")
                self._comps.stop_component_instance(self)

            # errors happen fairly often, keep going
            self._logger.error("DHT22: Can't read sensor - %s", str(error))
            return
        self._error_num = 0

        self._set_humidity(humidity)
        self._set_temperature(temperature)

        self._logger.debug("DHT22: Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(
            temperature, humidity))

    def stop(self):  # override Component
        super().stop()
        if self._sensor_driver:
            self._sensor_driver.exit()
            del self._sensor_driver
            pid = os.system("pgrep libgpiod_pulsei")  # n not needed at the end??
            if pid:
                os.system("kill " + str(pid))


class BMP280(TempSensor, BarometricSensor, HumiditySensor, CyclicComponent):
    """
    Implements access to the BMP280 temperature/pressure sensor.
    """
    UPDATE_TIME = 5  # in seconds
    MEASURE_POINTS = 5

    def __init__(self):
        super().__init__()
        self._sensor_driver = None
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        """
        Initialize sensor (simply save the module), no complicated init needed.
        """
        # use the old Adafruit driver, the new one is more unstable
        import Adafruit_BME280  # pylint: disable=import-outside-toplevel
        self._sensor_driver = Adafruit_BME280.BME280()

    def _read_sensor(self):
        """
        Reads the actual values in the moving average list.
        Ignores comm. errors, but does simple value validity checks.
        """
        temperature = 0
        pressure = 0
        humidity = 0
        try:
            temperature = self._sensor_driver.read_temperature()
            pressure = self._sensor_driver.read_pressure() / 100  # Pa to hPa
            humidity = self._sensor_driver.read_humidity()
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("BMP280: Can't read sensor - %s", str(error))
            return

        self._set_pressure(pressure)
        self._set_temperature(temperature)
        self._set_humidity(humidity)

        self._logger.debug("BMP280: Temp={0:0.1f}*C  Pressure={1}% Humidity={2:0.1f}%".format(
            temperature, pressure, humidity))


class MH_Z19(CO2Sensor, TempSensor, CyclicComponent):  # pylint: disable=invalid-name
    """
    Implements access to the MH-Z19 CO2 sensor.
    Return the values as a moving average of the last points.
    """
    UPDATE_TIME = 3  # in seconds
    MEASURE_POINTS = 3
    STABILIZE_TIME = 10  # in minutes

    def __init__(self):
        super().__init__()
        self._start_time = datetime.datetime.now()
        self._readings_stabilized = False
        self._sensor_driver = False
        self._start_update_loop(self._init_sensor, self._read_sensor)

    def _init_sensor(self):
        import mh_z19  # pylint: disable=import-outside-toplevel
        if self._runtime_system.is_target_system:
            # check for enabled serial port in boot config
            boot_config: str = check_output(["sudo", "cat", "/boot/config.txt"]).decode("utf-8")
            lines = boot_config.splitlines()
            # enable access to the needed serial device - is rpi version dependent
            os.system("sudo systemctl mask serial-getty@" + mh_z19.partial_serial_dev + ".service")
            for line in lines:
                if line.replace(" ", "") == "enable_uart=0":
                    # set enable_uart to 1
                    os.system("sudo sed -i 's/^.*enable_uart=.*$/enable_uart=1/g' /boot/config.txt")
                    # restart to enable modifications
                    self._runtime_system.restart()
            mh_z19.detection_range_5000()
        self._sensor_driver = mh_z19

    def _read_sensor(self):
        temperature = 0
        co2 = 0
        try:
            values = self._sensor_driver.read_all()
            temperature = values.get("temperature")
            co2 = values.get("co2")
        except Exception as error:
            # errors happen fairly often, keep going
            self._logger.error("MH-Z19: Can't read sensor - %s", str(error))
            return

        self._set_temperature(temperature)
        self._set_co2(co2)

        # eval stabilizer time
        if datetime.datetime.now() > self._start_time + datetime.timedelta(minutes=self.STABILIZE_TIME):
            self._readings_stabilized = True

        # log if value is readable
        self._logger.debug(
            'MH-Z19: Temp={0:0.1f}*C  CO2={1:0.1f}ppm'.format(values.get("temperature"), co2))


# class CCS811(CO2Sensor, TvocSensor, CyclicComponent):  # pylint: disable=invalid-name
    # """
    # Implements access to the CCS811 CO2/TVOC sensor.
    # Return the values as a moving average of the last points.
    # """
    # UPDATE_TIME = 3  # in seconds
    # MEASURE_POINTS = 3
    # MIN_CO2_VALUE = 400  # for validity check
    # MAX_CO2_VALUE = 6000  # for validity check

    # def __init__(self, components: ComponentRegistry):
        # CO2Sensor.__init__(self)
        # TvocSensor.__init__(self)
        # CyclicComponent.__init__(self, components)

        # self._reload_forbidden = True
        # self._sensor_driver: "CCS811" = None
        # self._error_num = 0

        # self._start_update_loop(self._init_sensor, self._read_sensor)

    # def _init_sensor(self):
        # """
        # Inits driver and tries to communicate.
        # Imports the real driver only on target platform.
        # """
        # if self._runtime_system.is_target_system:
            # from piweather.driver.ccs811 import CCS811  # pylint: disable=import-outside-toplevel
        # else:  # load mock
            # from ccs811 import CCS811  # pylint: disable=import-outside-toplevel
        # try:
            # self._sensor_driver = CCS811()

            # # wait for the sensor to be ready - try max 3 times
            # i = 0
            # while not self._sensor_driver.read_ready() and i <= 3:
                # i += 1
                # time.sleep(1)
        # except Exception as error:
            # self._logger.error("CCS811: can not be initialized - %s", str(error))
            # return

    # def _react_on_error(self):
        # if self._error_num == 2:
            # self._logger.error("CCS811: Error in reading sensor. Resetting ...")
            # if self._sensor_driver:
                # try:
                    # self._sensor_driver.reset()
                # except Exception as error:
                    # self._logger.error("CCS811: can not be resetted - %s", str(error))
                    # self._disabled = True  # TODO
            # else:  # driver failed to start (wiring issues?)
                # self._disabled = True  # TODO
        # if self._error_num == 3:
            # self._logger.error("CCS811: Error in reading sensor. Restarting...")
            # del self._sensor_driver
            # self._init_sensor()

    # def _set_environmental_values(self):
        # """
        # If there is a temperature/humidity sensor, it can be
        # used to initalize this sensor, so it has more accurate measurements
        # """
        # temperature = self._comps.temp_sensor.get_temperature()
        # humidity = self._comps.humidity_sensor.get_humidity()
        # # wait for values to stabilize
        # while not 15 < temperature < 50:
            # time.sleep(2)

        # self._sensor_driver.set_environmental_data(int(humidity), float(temperature))

    # def _read_sensor(self):
        # """
        # Cyclic function for reading the actual values into a moving average list.
        # Sets environment values from an optional temp/hum sensor.
        # Does a soft restart after 2 errors and a hard reset after 3 errors.
        # """
        # co2 = None
        # tvoc = None
        # try:
            # self._react_on_error()
            # if self._sensor_driver.read_ready():
                # co2 = self._sensor_driver.get_co2()
                # tvoc = self._sensor_driver.get_tvoc()
                # self._readings_stabilized = self._sensor_driver.readings_stabilized()
            # else:
                # self._error_num += 1
                # return

            # self._error_num = 0
        # except Exception as error:  # there are a miriad of errors...
            # self._error_num += 1
            # self._logger.error("CCS811: Error in reading sensor - %s", str(error))
            # return

        # self._set_co2(co2)
        # self._set_tvoc(tvoc)

        # # log if every value is readable
        # self._logger.debug('CCS811: CO2={0:0.1f}ppm TVOC={1:0.1f}'.format(co2, tvoc))


class SR501(Component):  # pylint: disable=invalid-name
    """ Implements access to the SR501 infrared movement sensor. """
    BOUNCE_TIME = 3

    def __init__(self, pin):
        super().__init__()
        self._pin = pin
        self._motion_detected = 0
        self._sensor_driver: "RPi.GPIO" = None

        Process = threading.Thread
        self._init_thread = Process(name="SR501_Init",
                                    target=self._register_callback,
                                    daemon=True)
        self._init_thread.start()

    def __del__(self):
        """ Cleanup GPIO """
        self._sensor_driver.setmode(self._sensor_driver.BCM)
        self._sensor_driver.remove_event_detect(self._pin)
        self._sensor_driver.cleanup()

    @property
    def motion_detected(self) -> bool:
        """ Returns true, if often motion was detected in the last 3 seconds. """
        return bool(self._motion_detected)

    def _register_callback(self):
        """ Initializer function, register the wake-up function to the configured pin."""
        import RPi.GPIO as GPIO  # pylint: disable=import-outside-toplevel
        self._sensor_driver = GPIO
        try:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self._pin, GPIO.IN)
            GPIO.add_event_detect(self._pin, GPIO.RISING,
                                  callback=self._wake_up_from_sensor,
                                  bouncetime=self.BOUNCE_TIME * 1000)
        except Exception as error:
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


class Prologue433(TempSensor, CyclicComponent):
    """ Dummy class for future implementation """

    def __init__(self):
        super().__init__()
        self._disabled = True
        self._is_active = None
        if not self.check_connection():
            return

    def check_connection(self):
        """ Check, if sensor can be found """
        self.is_active = False
