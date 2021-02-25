import time
import threading
#from piweather.settings import LOCATION, Settings
from piweather.components import sensors
from piweather.base.components import ComponentRegistry
from piweather.settings import Settings


def testDHT22(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)

    sensors.DHT22.MEASURE_POINTS = 2
    sensors.DHT22.UPDATE_TIME = 1
    sensor = sensors.DHT22(pin=10, components=comps)

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (sensor.MEASURE_POINTS + 1))

    from adafruit_dht import TEMP, HUM
    assert sensor.get_humidity() == HUM
    assert sensor.get_temperature() == TEMP


def testCCS811(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")

    comps = ComponentRegistry(settings)
    sensor = sensors.CCS811(comps)


def testMH_Z19(base_fixture, target_mockup_fixture):
    sensor = sensors.MH_Z19()


def testSR501(base_fixture, target_mockup_fixture):
    sensor = sensors.SR501(pin=8)
    assert not sensor.motion_detected
    import RPi.GPIO as GPIO
    # the call blocks, so use a thread
    t = threading.Thread(target=sensor._wake_up_from_sensor, args=[None, ])
    t.start()
    assert sensor.motion_detected
    t = threading.Thread(target=sensor._wake_up_from_sensor, args=[None, ])
    t.start()
    assert sensor.motion_detected == True
    assert sensor._motion_detected == 2


def testBMP280(base_fixture, target_mockup_fixture):
    from Adafruit_BME280 import TEMP, PRESSURE, HUMIDITY
    sensors.BMP280.MEASURE_POINTS = 2
    sensors.BMP280.UPDATE_TIME = 1

    sensor = sensors.BMP280()
    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (sensor.MEASURE_POINTS) + 1)
    assert sensor.get_pressure() == PRESSURE
    assert sensor.get_temperature() == TEMP
    assert sensor.get_humidity() == HUMIDITY


def testProlougeSensor(base_fixture):
    pass
