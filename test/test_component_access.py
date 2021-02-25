import logging
import time

from freezegun import freeze_time
from piweather.base.components import (Component, ComponentRegistry,
                                       CyclicComponent)
from piweather.base.system import RuntimeSystem
from piweather.settings import (MH_Z19_ENABLED, CCS811_ENABLED, BMP_280_ENABLED,
                                DHT_22_DISABLED, DHT_22_PIN,
                                MOTION_SENSOR_ENABLED, MOTION_SENSOR_PIN,
                                Settings)


def testDefaultComponentCreation(base_fixture, target_mockup_fixture):
    # test, that all components can be instantiated
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(DHT_22_PIN, 15)
    settings.set(BMP_280_ENABLED, True)

    comps = ComponentRegistry(settings)
    # dht22
    temp = comps.temp_sensor
    assert temp
    disp = comps.display
    assert disp
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


def testDHT22SensorInstances():
    pass

    # # bmp280
    # comps._sensors["TempSensor"] = None
    # settings.set(DHT_22_PIN, 0)  # disable
    # temp = comps.temp_sensor
    # assert temp


def testComponentRegistry(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    cr = ComponentRegistry(settings)
    assert not cr._unload_in_progress

    comp = cr.create_component_instance(Component)
    cyc_comp = cr.create_component_instance(CyclicComponent)
    assert isinstance(comp, Component)
    assert isinstance(cyc_comp, CyclicComponent)

    assert "Component" in cr.get_names()
    assert "CyclicComponent" in cr.get_names()

    assert cr.get("Component") == comp
    assert cr.get("CyclicComponent") == cyc_comp

    cr.stop_component("Component")
    cr.stop_component("CyclicComponent")


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

    comp = cr.create_component_instance(Component)
    cyc_comp = cr.create_component_instance(CyclicComponent)
    assert isinstance(comp, Component)
    assert isinstance(cyc_comp, CyclicComponent)

    assert "Component" in cr.get_names()
    assert "CyclicComponent" in cr.get_names()

    assert cr.get("Component") == comp
    assert cr.get("CyclicComponent") == cyc_comp

    cr.stop_component("Component")
    cr.stop_component("CyclicComponent")
