

import datetime
import json
import threading
import time
from pathlib import Path
from typing import List

import jsonschema
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import *
from piweather import config
from piweather.base.components import Component, ComponentRegistry
from piweather.base.logger import Logger
from piweather.resources import get_rsc_file
from piweather.settings import EVENTS_ENABLED, LANG, NIGHT_MODE_END, Settings
from tzlocal import get_localzone


class Event(object):
    """
    Model of an event form config file.
    """

    def __init__(self, name):
        self._name = name
        self._recurrence = None
        self._date = None
        self._triggers = []
        self._actions = {}
        self._last_triggered = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = new_value

    @property
    def recurrence(self):  # trigger, day, month, year
        return self._recurrence

    @recurrence.setter
    def recurrence(self, new_value: str):
        self._recurrence = new_value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, new_value: str):
        self._date = new_value

    @property
    def triggers(self):
        return self._triggers

    @triggers.setter
    def triggers(self, new_value: str):
        self._triggers = new_value

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, new_value: str):
        self._actions = new_value

    @property
    def last_triggered(self):
        return self._last_triggered

    @last_triggered.setter
    def last_triggered(self, new_value: str):
        self._last_triggered = new_value


def parse_event_file(events_file_path: Path) -> List[Event]:
    """ Parse the json config file, validate and convert to object structure """
    events: List[Event] = []
    Logger().info(f"Loading file '{events_file_path}'...")

    if not events_file_path.is_file():
        Logger().error(f"Config file '{events_file_path}' does not exist.")
        return []
    with open(events_file_path, encoding="utf-8") as config_file:
        try:
            events_config = json.load(config_file)
            with open(get_rsc_file("base", "events_schema")) as schema_file:
                json_schema = json.load(schema_file)
                jsonschema.validate(instance=events_config, schema=json_schema)
        except BaseException as error:
            Logger().error(f"Config file:\n{str(error)}")
            return []

    for event_data in events_config.get("events", []):
        event = Event(event_data.get("name", ""))
        event.triggers = event_data.get("triggers", "")
        event.actions = event_data.get("actions", "")
        event.recurrence = event_data.get("recurrence", "")
        event.date = event_data.get("date", "")
        event.last_triggered = event_data.get("last_triggered", "")
        events.append(event)
    return events


def write_events_file(events_file_path: Path, events: List[Event]):
    # create json dict from model
    events_data = []
    for event in events:
        event_data = {"name": event.name, "recurrence": event.recurrence,
                      "date": event.date, "triggers": event.triggers,
                      "actions": event.actions, "last_triggered": event.last_triggered}
        events_data.append(event_data)

    # get last version
    with open(get_rsc_file("base", "events_schema")) as schema_file:
        json_schema = json.load(schema_file)
    version = json_schema.get("properties").get("version").get("enum")[-1]
    events_config = {"version": version, "events": events_data}
    try:
        with open(events_file_path, "w") as config_file:
            json.dump(events_config, config_file, indent=4)
    except Exception:
        print("Cannot open events.json file")


def day_time_greeting() -> str:
    current_date_time = datetime.datetime.now()
    current_time = current_date_time.time()
    time_of_day = ""
    # currently hardcoded to german definitions
    if datetime.time(hour=6) <= current_time < datetime.time(hour=10):
        time_of_day = "morning"
    elif datetime.time(hour=10) <= current_time < datetime.time(hour=12):
        time_of_day = "beforenoon"
    elif datetime.time(hour=12) <= current_time < datetime.time(hour=14):
        time_of_day = "noon"
    elif datetime.time(hour=14) <= current_time < datetime.time(hour=17):
        time_of_day = "afternoon"
    elif datetime.time(hour=17) <= current_time < datetime.time(hour=21):
        time_of_day = "evening"
    elif datetime.time(hour=21) <= current_time:
        time_of_day = "night"
    elif current_time < datetime.time(hour=6):
        time_of_day = "night"
    if not time_of_day:
        Exception("ERROR getting time of day at " + str(current_time))
    return time_of_day


class EventHandler(Component):
    """
    Scheduler for configured events.
    """

    def __init__(self,  components: ComponentRegistry, settings: Settings):
        super().__init__(components, settings)
        if not settings.get(EVENTS_ENABLED):
            return

        self.gui_background_update_sig = None
        self._config_events_file = config.base_path / "events.json"
        self._events = parse_event_file(self._config_events_file)
        self._scheduler = None

        self._init_thread = threading.Thread(
            name="StartScheduler", target=self._init_scheduler, daemon=True)
        self._init_thread.start()

    def stop(self):
        self._scheduler.shutdown(wait=False)

    def _init_scheduler(self):
        self._scheduler = BackgroundScheduler()
        self._scheduler.configure(job_defaults={"misfire_grace_time": 3, "max_instances": 1})
        for event in self._events:
            self._register_event(event)
        self._scheduler.start()

    def _register_event(self, event: Event):
        self._logger.debug("EventHandler: Registering " + event.name)
        current_date_time = datetime.datetime.now()
        # Determine, if it would have run today, so it can be scheduled for immediate execution
        would_run_today = False
        if event.recurrence != "date":  # daily exec
            day_of_week_to_run = "*"
            if event.recurrence == "day":
                would_run_today = True
            elif event.recurrence == "weekday":
                day_of_week_to_run = "mon–fri"
                if current_date_time.isoweekday() < 6:
                    would_run_today = True
            job = self._scheduler.add_job(self._start_execute_event, name=event.name, args=[event], trigger="cron",
                                          day_of_week=day_of_week_to_run, hour=self._settings.get(NIGHT_MODE_END))
        elif event.recurrence == "date":
            try:
                date_obj = parse_date(event.date)
            except Exception as error:
                self._logger.error(f"EvenHandler: Cannot read date for {event.name}: " + str(error))

            time_delta = current_date_time - date_obj
            if time_delta.days == 0:
                would_run_today = True
            job = self._scheduler.add_job(self._start_execute_event, name=event.name, args=[event], trigger="cron", month=date_obj.month, day=date_obj.day, hour=date_obj.hour,
                                          minute=date_obj.minute)
        # check immediatly executable jobs
        if event.triggers or "background" in event.actions:
            if not would_run_today:
                return
            time_delta = None
            # now check, if it has already run
            if event.last_triggered:
                date_obj = parse_date(event.last_triggered)
                time_delta = current_date_time - date_obj
            if not time_delta or time_delta.days >= 0:
                direct_event = Event(event.name + "_direct_exec")
                # only init with actions
                direct_event.actions = event.actions
                self._logger.debug("EventHandler: Registering for direct exec " + direct_event.name)
                self._scheduler.add_job(
                    self._start_execute_event, name=direct_event.name, args=[direct_event])

    def _start_execute_event(self, event):
        thread = threading.Thread(
            name="ExecuteEvent_" + event.name, target=self._execute_event, args=[event, ], daemon=True)
        thread.start()

    def _execute_event(self, event: Event):
        self._logger.debug("EventHandler: Executing now " + event.name)
        current_date_time = datetime.datetime.now()

        if "background" in event.actions:
            # wait for gui signal to be registered
            while not self.gui_background_update_sig:
                time.sleep(1)
            self.gui_background_update_sig.emit(event.actions.get("background"))
            self._logger.debug("EventHandler: Setting bgr to " + event.actions.get("background"))

            # schedule internal reset event for the next day at midnight
            reset_event = Event(event.name + "_reset")
            reset_event.actions["background"] = "background_s.png"
            new_date = current_date_time + relativedelta(days=+1)
            self._scheduler.add_job(self._start_execute_event, name=reset_event.name, args=[
                                    reset_event], trigger="cron", start_date=current_date_time, year=new_date.year,  month=new_date.month,
                                    day=new_date.day)

        if "text_2_speach" in event.actions:
            if "motion" in event.triggers:  # wait for motion sensor to trigger
                # timeout is the next day
                new_date = current_date_time + relativedelta(days=+1)
                while (not(not self._comps.energy_saver.night_mode_active and self._comps.energy_saver.is_awake)
                       and current_date_time < new_date):
                    time.sleep(2)
                    current_date_time = datetime.datetime.now()

            text = event.actions.get("text_2_speach")
            if text:  # replace known patterns
                text = text.replace("${day_time_greeting}", self._comps.tts.get_tts_string(
                    day_time_greeting(), self._settings.get(LANG)))

            self._comps.tts.say(text, self._settings.get(LANG))

        if "play_sound" in event.actions:
            self._comps.sound.play(event.actions.get("play_sound"))

        event.last_triggered = str(datetime.datetime.now())
        write_events_file(self._config_events_file, self._events)
