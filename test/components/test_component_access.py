import logging
import time

from freezegun import freeze_time
from waqd.base.component_reg import (Component, ComponentRegistry,
                                       CyclicComponent)
from waqd.settings import (BME_280_ENABLED, DHT_22_PIN, MOTION_SENSOR_ENABLED, Settings)


def testDefaultComponentCreation(base_fixture, target_mockup_fixture):
    # test, that all components can be instantiated
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(DHT_22_PIN, 15)
    settings.set(BME_280_ENABLED, True)

    comps = ComponentRegistry(settings)
   
    disp = comps.display
    assert disp
    temp = comps.temp_sensor
    assert temp
    mot = comps.motion_detection_sensor
    assert mot
    tts = comps.tts
    assert tts
    es = comps.energy_saver
    assert es
    weather_info = comps.weather_info
    assert weather_info
    au = comps.auto_updater
    assert au
    hum = comps.humidity_sensor
    assert hum
    ps = comps.pressure_sensor
    assert ps
    co2 = comps.co2_sensor
    assert co2
    tvoc = comps.tvoc_sensor
    assert tvoc
    rt = comps.remote_temp_sensor
    assert rt
    ev = comps.event_handler
    assert ev

# TODO Add stop component test

def testComponentRestartWatchdog(base_fixture, target_mockup_fixture):
    # test, that a sensor revives after stopping it
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(DHT_22_PIN, 15)

    comps = ComponentRegistry(settings)
    temp = comps.temp_sensor
    hum = comps.humidity_sensor
    assert temp

    comps.stop_component_instance(temp)
    time.sleep(1)
    assert not hasattr(comps._components, "DHT22")
    assert not hasattr(comps._components, "TempSensor")
    assert not hasattr(comps._components, "HumiditySensor")

    assert comps.temp_sensor
    assert comps.humidity_sensor
    assert comps._components["DHT22"]

def testComponentRegistry(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    cr = ComponentRegistry(settings)
    assert not cr._unload_in_progress

    comp = cr._create_component_instance(Component)
    cyc_comp = cr._create_component_instance(CyclicComponent)
    assert isinstance(comp, Component)
    assert isinstance(cyc_comp, CyclicComponent)

    assert "Component" in cr.get_names()
    assert "CyclicComponent" in cr.get_names()

    assert cr._components["Component"] == comp
    assert cr._components["CyclicComponent"] == cyc_comp


def testComponentRegistryDefaultSensors(base_fixture):

    # disable every hw sensor
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(DHT_22_PIN, 0)
    # settings.set() = 0

    cr = ComponentRegistry(settings)


def testComponentRegistryDefaultComps(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    TestComponent = Component(settings=settings)
    cr = ComponentRegistry(settings)
    assert not cr._unload_in_progress

    comp = cr._create_component_instance(Component)
    cyc_comp = cr._create_component_instance(CyclicComponent)
    assert isinstance(comp, Component)
    assert isinstance(cyc_comp, CyclicComponent)

    assert "Component" in cr.get_names()
    assert "CyclicComponent" in cr.get_names()

    assert cr._components["Component"] == comp
    assert cr._components["CyclicComponent"] == cyc_comp
