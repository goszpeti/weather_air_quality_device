import pint
import time
from threading import Thread

from waqd.components import sensors
from waqd.base.component_reg import ComponentRegistry
from waqd.settings import LOG_SENSOR_DATA, Settings
from waqd.base.system import RuntimeSystem

from test.conftest import mock_run_on_non_target
import waqd.app as app


def test_max_delta(base_fixture, target_mockup_fixture, capsys):

    ureg = pint.UnitRegistry()
    ureg.define('fraction = [] = frac')
    ureg.define('percent = 1e-2 frac = pct')
    ureg.define('ppm = 1e-6 fraction')

    print(ureg.Quantity('100 pct').to('dimensionless'))
    print(ureg('0.5 dimensionless').to('pct'))
    print(ureg('pct').to('ppm'))
    print(ureg('1e4 ppm').to('pct'))
    import adafruit_dht
    settings = Settings(base_fixture.testdata_path / "integration")
    sensor = sensors.TempSensor(False, 2)
    sensor._temp_impl._values = [22]  # default value
    sensor._set_temperature(22)  # first value written check
    sensor._set_temperature(59)
    sensor._set_temperature(59)

    temp_value = sensor.get_temperature()
    captured = capsys.readouterr()
    text = captured.out
    assert temp_value.m_as(app.unit_reg.degC) == adafruit_dht.TEMP


def test_dht22(base_fixture, target_mockup_fixture):
    from adafruit_dht import TEMP, HUM
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)
    measure_points = 2
    sensors.DHT22.MEASURE_POINTS = measure_points
    sensors.DHT22.UPDATE_TIME = 1
    sensor = sensors.DHT22(pin=22, components=comps, settings=settings)

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    time.sleep(sensor.UPDATE_TIME * (measure_points + 1))

    assert sensor.get_humidity().magnitude == HUM
    assert sensor.get_temperature().magnitude == TEMP


def test_ccs811(base_fixture, target_mockup_fixture):
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
    assert sensor.get_tvoc().magnitude == TVOC
    assert sensor.get_co2().magnitude == 1000


def test_mh_z19(base_fixture, target_mockup_fixture, mocker):
    mock_run_on_non_target(mocker)
    assert not RuntimeSystem().is_target_system
    settings = Settings(base_fixture.testdata_path / "integration")
    sensors.MH_Z19.MEASURE_POINTS = 2
    sensor = sensors.MH_Z19(settings)

    time.sleep(1)
    assert sensor.is_alive
    assert sensor.is_ready

    # wait until all measurement points are filled up, so that mean value equals the constant value
    # -> takes too long, every call spawns a new python process takes a few seconds
    time.sleep(sensor.UPDATE_TIME * (sensors.MH_Z19.MEASURE_POINTS + 1))
    from mh_z19 import CO2
    assert sensor.get_co2().magnitude == 735


def test_sr501(base_fixture, target_mockup_fixture, mocker):
    sensor = sensors.SR501(pin=8)  # TODO get from CI config file
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
    assert sensor.get_temperature().magnitude == 28.4
    assert sensor.get_humidity().magnitude == HUMIDITY
    assert sensor.get_pressure().magnitude >= PRESSURE  # adjusted for location


def test_bmp280(base_fixture, target_mockup_fixture):
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
    assert sensor.get_temperature().magnitude == 28.4
    assert sensor.get_pressure().magnitude >= PRESSURE  # adjusted for location
