
import time
from freezegun import freeze_time

from waqd.components.power import (BRIGHTNESS, DAY_STANDBY_TIMEOUT,
                                        MOTION_SENSOR_ENABLED,
                                        NIGHT_MODE_BEGIN,
                                        NIGHT_MODE_BRIGHTNESS, NIGHT_MODE_END,
                                        NIGHT_STANDBY_TIMEOUT,
                                        NIGHTMODE_WAKEUP_DELTA_BRIGHTNESS,
                                        STANDBY_BRIGHTNESS, ESaver)
from waqd.settings import Settings
from waqd.base.components import ComponentRegistry


def testNoStandbyIfSensorIsDisabled(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, False)
    settings.set(NIGHT_MODE_BEGIN, 23)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)

    energy_saver = None
    comps = ComponentRegistry(settings)
    disp = comps.display

    # night mode - no wakeup
    with freeze_time("2019-01-01 12:00:00"):
        # energy_saver needs to be initalized in freeze time, otherwise testing time will have an impact
        energy_saver = ESaver(comps, settings)
        time.sleep(energy_saver.INIT_WAIT_TIME)
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert disp.get_brightness() == settings.get(BRIGHTNESS)

    energy_saver.stop()


def testNightModeStartup(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(NIGHT_MODE_BEGIN, 23)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)
    # night
    with freeze_time("2019-01-01 01:59:59"):
        energy_saver = None
        comps = ComponentRegistry(settings)
        disp = comps.display
        energy_saver = ESaver(comps, settings)
        time.sleep(energy_saver.INIT_WAIT_TIME)
        assert not energy_saver._update_thread is None
        assert not energy_saver.night_mode_active
        assert disp.get_brightness() == 70
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS
        assert energy_saver.night_mode_active

    with freeze_time("2019-01-01 02:00:01"):
        time.sleep(2 * energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS

    with freeze_time("2019-01-02 04:59:01"):
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS

    energy_saver.stop()


def testNightModeEnter(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(NIGHT_MODE_BEGIN, 23)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)

    energy_saver = None
    comps = ComponentRegistry(settings)
    disp = comps.display
    # day
    with freeze_time("2019-01-01 22:59:59"):
        energy_saver = ESaver(comps, settings)
        time.sleep(energy_saver.INIT_WAIT_TIME)
        assert not energy_saver._update_thread is None
        assert not energy_saver.night_mode_active
        assert disp.get_brightness() == 70
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert disp.get_brightness() == STANDBY_BRIGHTNESS
        assert not energy_saver.night_mode_active

    with freeze_time("2019-01-01 23:00:01"):
        time.sleep(2 * energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS

    with freeze_time("2019-01-02 04:59:01"):
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS

    energy_saver.stop()


def testDayModeEnter(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(NIGHT_MODE_BEGIN, 22)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)

    energy_saver = None
    comps = ComponentRegistry(settings)
    disp = comps.display

    with freeze_time("2019-01-01 22:59:59"):
        energy_saver = ESaver(comps, settings)
        time.sleep(energy_saver.INIT_WAIT_TIME)
        assert not energy_saver._update_thread is None
        assert 70 == disp.get_brightness()
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS
        assert energy_saver.night_mode_active == True

    with freeze_time("2019-01-02 05:00:01"):
        time.sleep(2 * energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active == False
        assert disp.get_brightness() == STANDBY_BRIGHTNESS

    with freeze_time("2019-01-02 21:59:01"):
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active == False
        assert disp.get_brightness() == STANDBY_BRIGHTNESS

    energy_saver.stop()


def testWakeUpFromNightMode(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")

    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(NIGHT_MODE_BEGIN, 22)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)
    settings.set(NIGHT_STANDBY_TIMEOUT, 10)

    energy_saver = None
    comps = ComponentRegistry(settings)
    disp = comps.display

    with freeze_time("2019-01-01 22:59:59"):
        energy_saver = ESaver(comps, settings)
        time.sleep(energy_saver.INIT_WAIT_TIME)
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert NIGHT_MODE_BRIGHTNESS == disp.get_brightness()
        assert energy_saver.night_mode_active == True

        # set sensor high
        comps.motion_detection_sensor._motion_detected = 1
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert disp.get_brightness() == 70 - NIGHTMODE_WAKEUP_DELTA_BRIGHTNESS

        # set sensor low
        comps.motion_detection_sensor._motion_detected = 0
        time.sleep(10 + 1)
        assert disp.get_brightness() == NIGHT_MODE_BRIGHTNESS

    energy_saver.stop()


def testStandbyInDayMode(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(MOTION_SENSOR_ENABLED, True)
    settings.set(NIGHT_MODE_BEGIN, 22)
    settings.set(NIGHT_MODE_END, 5)
    settings.set(BRIGHTNESS, 70)
    settings.set(DAY_STANDBY_TIMEOUT, 10)

    energy_saver = None
    comps = ComponentRegistry(settings)
    disp = comps.display

    # day
    with freeze_time("2019-01-01 12:59:59"):
        energy_saver = comps.energy_saver
        time.sleep(energy_saver.INIT_WAIT_TIME)
        time.sleep(energy_saver.UPDATE_TIME + 1)
        assert energy_saver.night_mode_active == False
        assert disp.get_brightness() == STANDBY_BRIGHTNESS

    # switch to wake
    comps.motion_detection_sensor._motion_detected = 1
    with freeze_time("2019-01-01 13:00:10"):
        time.sleep(energy_saver.UPDATE_TIME + 2)
        assert disp.get_brightness() == settings.get(BRIGHTNESS)
        time.sleep(10 - energy_saver.UPDATE_TIME)
        # switch to standby
        comps.motion_detection_sensor._motion_detected = 0
        time.sleep(energy_saver.UPDATE_TIME * 2)
        assert disp.get_brightness() == STANDBY_BRIGHTNESS
    energy_saver.stop()
