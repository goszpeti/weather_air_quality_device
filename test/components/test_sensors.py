import time
from threading import Thread

from waqd.components import sensors
from waqd.base.component_reg import ComponentRegistry
from waqd.settings import Settings
from waqd.base.system import RuntimeSystem

from test.conftest import mock_run_on_non_target

def testDHT22(base_fixture, target_mockup_fixture):
    from adafruit_dht import TEMP, HUM
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)
    measure_points = 2
    sensors.DHT22.M = measure_points
    sensors.DHT22.UPDATE_TIME = 1
    sensor = sensors.DHT22(pin=22, components=comps, settings=settings)

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (measure_points + 1))

    assert sensor.get_humidity() == HUM
    assert sensor.get_temperature().m == TEMP


def testCCS811(base_fixture, target_mockup_fixture):
    from adafruit_ccs811 import TVOC, CO2
    settings = Settings(base_fixture.testdata_path / "integration")
    measure_points = 2
    sensors.CCS811.MEASURE_POINTS = measure_points
    comps = ComponentRegistry(settings)
    sensor = sensors.CCS811(comps, settings)
    # disable max delta, otherwise default value will not rise

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (measure_points + 1))
    assert sensor.get_tvoc() == TVOC
    assert sensor.get_co2() == CO2


def testMH_Z19(base_fixture, target_mockup_fixture, mocker):
    mock_run_on_non_target(mocker)
    assert not RuntimeSystem().is_target_system
    settings = Settings(base_fixture.testdata_path / "integration")
    measure_points = 2
    sensors.MH_Z19.MEASURE_POINTS = measure_points
    sensor = sensors.MH_Z19(settings)

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    # -> takes too long, every call spawns a new python process tgis takes a few seconds
    time.sleep(sensor.UPDATE_TIME * (measure_points + 1))
    from mh_z19 import CO2
    assert sensor.get_co2() == CO2


def testSR501(base_fixture, target_mockup_fixture, mocker):
    sensor = sensors.SR501(pin=8) # TODO get from CI config file
    assert not sensor.motion_detected
    # the call blocks, so use a thread
    wake_up_thread = Thread(target=sensor._wake_up_from_sensor, args=[None, ])
    wake_up_thread.start()
    assert sensor.motion_detected
    wake_up_thread = Thread(target=sensor._wake_up_from_sensor, args=[None, ])
    wake_up_thread.start()
    assert sensor.motion_detected == True
    assert sensor._motion_detected == 2


def testBME280(base_fixture, target_mockup_fixture):
    from adafruit_bme280.advanced import TEMP, PRESSURE, HUMIDITY
    settings = Settings(base_fixture.testdata_path / "integration")
    measure_points = 2
    sensors.BME280.UPDATE_TIME = 1
    sensors.BME280.MEASURE_POINTS = measure_points

    comps = ComponentRegistry(settings)
    sensor = sensors.BME280(comps, settings)
    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (sensor.MEASURE_POINTS + 1))
    assert sensor.get_temperature().m == TEMP
    assert sensor.get_humidity() == HUMIDITY
    assert sensor.get_pressure() >= PRESSURE  # adjusted for location


def testBMP280(base_fixture, target_mockup_fixture):
    from adafruit_bmp280 import TEMP, PRESSURE
    settings = Settings(base_fixture.testdata_path / "integration")

    measure_points = 2
    sensors.BMP280.MEASURE_POINTS = measure_points
    sensors.BMP280.UPDATE_TIME = 1

    comps = ComponentRegistry(settings)
    sensor = sensors.BMP280(comps, settings)
    
    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (measure_points + 1))
    assert sensor.get_temperature().m == TEMP
    assert sensor.get_pressure() >= PRESSURE  # adjusted for location


