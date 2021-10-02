import json
import tempfile
import time
from datetime import datetime

from freezegun import freeze_time

from waqd import config
from waqd.base.component_ctrl import ComponentController
from waqd.base.logger import Logger
from waqd.components.events import (EventHandler, get_time_of_day,
                                    parse_event_file, write_events_file)
from waqd.settings import (NIGHT_MODE_BEGIN, NIGHT_MODE_END, SOUND_ENABLED,
                           Settings)
from waqd.ui.main_ui import WeatherMainUi


def testParser(base_fixture, target_mockup_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SOUND_ENABLED, True)
    events = parse_event_file(base_fixture.testdata_path / "events" / "events.json")
    assert events
    assert events[0].name == "Daily Greeting"
    assert events[1].name == "Wakeup"
    temp_file = tempfile.gettempdir() + "/eventsTest.json"
    write_events_file(temp_file, events)
    with open(temp_file) as fp:
        events_read = json.load(fp)
    assert events_read.get("events")[0].get("name") == "Daily Greeting"
    assert events_read.get("events")[1].get("name") == "Wakeup"


def testDailyGreeting(base_fixture, qtbot, target_mockup_fixture, monkeypatch):

    with freeze_time(datetime(2020, 12, 29, 22, 59, 45), tick=True) as frozen:
        settings = Settings(base_fixture.testdata_path / "integration")
        settings.set(NIGHT_MODE_BEGIN, 22)
        settings.set(NIGHT_MODE_END, 0)
        settings.set(SOUND_ENABLED, True)
        comp_ctrl = ComponentController(settings)
        Logger().info("Start")
        comps = comp_ctrl.components
        comps.energy_saver
        wmu = WeatherMainUi(comp_ctrl, settings)
        from pytestqt.plugin import _qapp_instance
        config.qt_app = _qapp_instance
        qtbot.addWidget(wmu)
        ev = EventHandler(comps, settings)
        t = get_time_of_day()

        current_date_time = datetime.now()
        settings._logger.info(current_date_time)
        assert t
        ev.gui_background_update_sig = wmu.change_background_sig
        while not ev._scheduler:
            time.sleep(1)
        comps.motion_detection_sensor._motion_detected = 5

        time.sleep(20)

        #comps.motion_detection_sensor._motion_detected = 0
        #time.sleep(30)

        # TODO implement


def testEventScheduler(base_fixture, qtbot, target_mockup_fixture, monkeypatch):

    with freeze_time(datetime(2020, 12, 24, 22, 59, 45), tick=True) as frozen:
        settings = Settings(base_fixture.testdata_path / "integration")
        #settings.set(NIGHT_MODE_END, 0)
        settings.set(SOUND_ENABLED, True)
        comp_ctrl = ComponentController(settings)
        Logger().info("Start")
        comps = comp_ctrl.components
        comps.energy_saver
        wmu = WeatherMainUi(comp_ctrl, settings)
        from pytestqt.plugin import _qapp_instance
        config.qt_app = _qapp_instance
        qtbot.addWidget(wmu)
        #monkeypatch.setattr('apscheduler.triggers.date.datetime', frozen)
        ev = EventHandler(comps, settings)
        t = get_time_of_day()

        current_date_time = datetime.now()
        settings._logger.info(current_date_time)
        assert t
        ev.gui_background_update_sig = wmu.change_background_sig
        while not ev._scheduler:
            time.sleep(1)
        comps.motion_detection_sensor._motion_detected = 1
        time.sleep(8)

        comps.motion_detection_sensor._motion_detected = 0
        time.sleep(10)
        time.sleep(10)
        time.sleep(10)
        time.sleep(10)


    # with freeze_time("2020-12-24 22:59:57", tick=True):
    #     time.sleep(5)
    #     t = day_time_greeting()
    #     assert t
    #     time.sleep(5)

    # with freeze_time("2020-12-25 23:59:58", tick=True):
    #     time.sleep(5)
    #     t = day_time_greeting()
    #     assert t

    # with freeze_time("2020-12-25 06:59:45", tick=True):
    #     time.sleep(4)
    #     comps.motion_detection_sensor._motion_detected = 1
    #     time.sleep(6)

    # with freeze_time("2020-12-25 10:00:00", tick=True):
    #     comps.motion_detection_sensor._motion_detected = 1
    #     time.sleep(5)

    # with freeze_time("2020-12-28 00:00:00"):
    #     time.sleep(5)
