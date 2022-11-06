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


import datetime
import json
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, TYPE_CHECKING

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

import waqd
from waqd.assets import get_asset_file
from waqd.base.component import Component
from waqd.base.component_reg import ComponentRegistry
from waqd.base.logger import Logger

if TYPE_CHECKING:
    from PyQt5.QtCore import pyqtBoundSignal
    from apscheduler.schedulers.background import BackgroundScheduler


class Event():
    """
    Model of an event form config file.
    """

    def __init__(self, name):
        self._name = name
        self._recurrence = ""
        self._date = ""
        self._triggers = []
        self._actions = {}
        self._last_triggered = None

    @property
    def name(self):
        """ Event name to identify an event """
        return self._name

    @name.setter
    def name(self, new_value: str):
        self._name = new_value

    @property
    def recurrence(self):
        """ Can be # trigger, day, month, year """
        return self._recurrence

    @recurrence.setter
    def recurrence(self, new_value: str):
        self._recurrence = new_value

    @property
    def date(self):
        """
        A specific date to execute the event, in conjunction with recurrence.
        Almost any format will be parsed, only time like 7:00 too.
        """
        return self._date

    @date.setter
    def date(self, new_value: str):
        self._date = new_value

    @property
    def triggers(self):
        """ A trigger to instantly trigger an event, or execute to trigger a scheduled event.
        This can be hours after the actual scheduling.
        Currently only "motion" supported. """
        return self._triggers

    @triggers.setter
    def triggers(self, new_value: str):
        self._triggers = new_value

    @property
    def actions(self) -> Dict[str, str]:
        """ The actions to execute with the event. """
        return self._actions

    @actions.setter
    def actions(self, new_value:  Dict[str, str]):
        self._actions.update(new_value)

    @property
    def last_triggered(self):
        """
        Get the last triggered date as a string.
        Is used to prevent to execute already executed events for a day.
        """
        return self._last_triggered

    @last_triggered.setter
    def last_triggered(self, new_value: str):
        self._last_triggered = new_value


def parse_event_file(events_file_path: Path) -> List[Event]:
    """ Parse the json config file, validate and convert to object structure """
    events: List[Event] = []
    Logger().info(f"EventHandler: Loading file '{events_file_path}'...")

    if not events_file_path.is_file():
        Logger().warning(f"EventHandler: Config file '{events_file_path}' does not exist.")
        return []
    with open(events_file_path, encoding="utf-8") as config_file:
        try:
            events_config = json.load(config_file)
            with open(get_asset_file("base", "events_schema")) as schema_file:
                import jsonschema
                json_schema = json.load(schema_file)
                jsonschema.validate(instance=events_config, schema=json_schema)
        except BaseException as error:
            Logger().error(f"EventHandler: Config file:\n{str(error)}")
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
    """ Write out the json dict from model """
    events_data = []
    for event in events:
        event_data = {"name": event.name, "recurrence": event.recurrence,
                      "date": event.date, "triggers": event.triggers,
                      "actions": event.actions, "last_triggered": event.last_triggered}
        events_data.append(event_data)

    # get last version
    with open(get_asset_file("base", "events_schema")) as schema_file:
        json_schema = json.load(schema_file)
    version = json_schema.get("properties").get("version").get("enum")[-1]
    events_config = {"version": version, "events": events_data}
    try:
        with open(events_file_path, "w") as config_file:
            json.dump(events_config, config_file, indent=4)
    except Exception:
        Logger().error("EventHandler: Cannot open events.json file")


def get_time_of_day() -> str:
    """ Helper function to get a day time specific greeting """
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

    def __init__(self,  components: ComponentRegistry, lang: str, night_mode_end: int, enabled=True):
        super().__init__(components, enabled=enabled)

        self._scheduler: Optional["BackgroundScheduler"] = None
        if not enabled:
            return
        self._lang = lang
        self._night_mode_end = night_mode_end
        self.gui_background_update_sig: Optional["pyqtBoundSignal"] = None
        self._config_events_file = waqd.user_config_dir / "events.json"
        self._events = parse_event_file(self._config_events_file)

        self._init_thread = threading.Thread(
            name="StartScheduler", target=self._init_scheduler, daemon=True)
        self._init_thread.start()

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)

    def _init_scheduler(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        self._scheduler = BackgroundScheduler()
        self._scheduler.configure(job_defaults={"misfire_grace_time": 3, "max_instances": 1})
        for event in self._events:
            self._register_event(event)
        self._scheduler.start()
        self._ready = True

    def _register_event(self, event: Event):
        self._logger.debug("EventHandler: Registering " + event.name)
        assert self._scheduler, "Internal components not available."
        current_date_time = datetime.datetime.now()
        # Determine, if it would have run today, so it can be scheduled for immediate execution
        # immediate exec does not log last exec!
        would_run_today = False
        if event.recurrence != "date":  # daily exec
            day_of_week_to_run = "*"
            if event.recurrence == "day":
                would_run_today = True
            elif event.recurrence == "weekday":
                day_of_week_to_run = "mon–fri"
                if current_date_time.isoweekday() < 6:
                    would_run_today = True
            self._scheduler.add_job(self._start_execute_event, name=event.name, args=[event],
                                    trigger="cron", day_of_week=day_of_week_to_run,
                                    hour=self._night_mode_end)
        elif event.recurrence == "date":
            date_obj = None
            try:
                date_obj = parse_date(event.date)
            except Exception as error:
                self._logger.error(f"EvenHandler: Cannot read date for {event.name}: " + str(error))
                return

            time_delta = current_date_time - date_obj
            if time_delta.days == 0:
                would_run_today = True
            self._scheduler.add_job(self._start_execute_event, name=event.name, args=[event],
                                    trigger="cron", month=date_obj.month, day=date_obj.day,
                                    hour=date_obj.hour, minute=date_obj.minute)
        # check immediatly executable jobs
        if event.triggers or "background" in event.actions:
            if not would_run_today:
                return
            time_delta = datetime.timedelta()
            # now check, if it has already run
            if event.last_triggered:
                date_obj = parse_date(event.last_triggered)
                time_delta = current_date_time - date_obj
            if time_delta.days >= 0:
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
        assert self._scheduler and self._comps, "Internal components not available."

        current_date_time = datetime.datetime.now()
        if "background" in event.actions:
            # wait for gui signal to be registered
            while not self.gui_background_update_sig:
                time.sleep(1)
            self.gui_background_update_sig.emit(event.actions.get("background"))
            self._logger.debug("EventHandler: Setting bgr to %s", event.actions.get("background"))

            # schedule internal reset event for the next day at midnight
            reset_event = Event(event.name + "_reset")
            reset_event.actions["background"] = "background_s.png"
            new_date = current_date_time + relativedelta(days=+1)
            self._scheduler.add_job(self._start_execute_event, name=reset_event.name, args=[
                                    reset_event],
                                    trigger="cron", start_date=current_date_time,
                                    year=new_date.year, month=new_date.month, day=new_date.day)

        if "text_2_speach" in event.actions:
            if "motion" in event.triggers:  # wait for motion sensor to trigger
                # timeout is the next day
                new_date = current_date_time + relativedelta(days=+1)
                while (not(not self._comps.energy_saver.night_mode_active and self._comps.energy_saver.is_awake)
                       and current_date_time < new_date):
                    time.sleep(2)
                    current_date_time = datetime.datetime.now()

            text = event.actions.get("text_2_speach", "")
            if text:  # replace known patterns
                text = text.replace("${day_time_greeting}", self._comps.tts.get_tts_string(
                    get_time_of_day(), self._lang))

            self._comps.tts.say(text, self._lang)

        if "play_sound" in event.actions:
            sound = event.actions.get("play_sound", "")
            self._comps.sound.play(Path(sound))

        event.last_triggered = str(datetime.datetime.now())
        write_events_file(self._config_events_file, self._events)
