
import datetime
from threading import Timer
import time

from waqd.base.component_reg import ComponentRegistry, CyclicComponent
from waqd.settings import (BRIGHTNESS, DAY_STANDBY_TIMEOUT,
                                MOTION_SENSOR_ENABLED, NIGHT_MODE_BEGIN,
                                NIGHT_MODE_END, NIGHT_STANDBY_TIMEOUT)
from waqd.settings.settings import Settings

STANDBY_BRIGHTNESS = 20
NIGHT_MODE_BRIGHTNESS = 0
NIGHT_STANDBY_BRIGHTNESS = 10
NIGHTMODE_WAKEUP_DELTA_BRIGHTNESS = 20


class ESaver(CyclicComponent):
    """
    Energy saver class  to manage the display day/night switch feature and
    wake-up/standby from motion sensor.
    """
    # TODO event based wake up and increase updatetime to 60 s
    INIT_WAIT_TIME = 5
    UPDATE_TIME = 2

    def __init__(self, components: ComponentRegistry, settings):
        super().__init__(components, settings)
        self._settings: Settings
        self._comps: ComponentRegistry

        self._night_mode_active = False
        self._is_awake = False
        self._sleep_timer = None
        self._start_update_loop(update_func=self._set_day_night_mode)
        self._ready = True
        self._previous_state = ""

    @property
    def is_awake(self):
        """ Display is in awake mode (higher brightness) """
        motion_detected = self._comps.motion_detection_sensor.motion_detected
        return self._is_awake or motion_detected
    
    @property
    def night_mode_active(self):
        """ Return true, if current time is im the timeframe set up in settings """
        return self._night_mode_active
    
    def wake_up(self, seconds: float):
        self._is_awake = True
        self._sleep_timer = Timer(seconds, self.sleep)
        self._sleep_timer.start()

    def sleep(self):
        self._is_awake = False

    def _set_day_night_mode(self):
        """ Runs periodically. Does the actual switch between the modes and sets brightness """
        # get value from motion sensor - if available
        if self._settings.get_bool(MOTION_SENSOR_ENABLED):
            NIGHT_MODE_BRIGHTNESS = 0
        else:
            NIGHT_MODE_BRIGHTNESS = NIGHT_STANDBY_BRIGHTNESS

        # determine sleep and wake time
        current_date_time = datetime.datetime.now()
        temp_time = datetime.datetime(current_date_time.year, current_date_time.month,
                                      current_date_time.day, 0, 0)

        sleep_time = temp_time + \
            datetime.timedelta(hours=self._settings.get_int(NIGHT_MODE_BEGIN))

        wake_time = temp_time + \
            datetime.timedelta(hours=self._settings.get_int(NIGHT_MODE_END))

        last_minute_today = temp_time + \
            datetime.timedelta(hours=23, minutes=59, seconds=59)

        is_before_midnight = current_date_time < last_minute_today
        if sleep_time.hour > wake_time.hour and current_date_time > sleep_time and is_before_midnight:
            wake_time = wake_time + datetime.timedelta(days=1)
        elif sleep_time.hour < wake_time.hour and current_date_time > wake_time and is_before_midnight:
            sleep_time = sleep_time + datetime.timedelta(days=1)

        # last exit point, to not vibrate screenon stop event
        if self._ticker_event.is_set():
            return

        # switch through the different modes
        previous_night_mode_active = self._night_mode_active
        if self.is_awake:  # wake from motion sensor
            if self.night_mode_active:
                self._logger.debug("ESaver: Wake-up at night")
                self._comps.display.set_brightness(
                    self._settings.get_int(BRIGHTNESS) - NIGHTMODE_WAKEUP_DELTA_BRIGHTNESS)
                time.sleep(self._settings.get_int(NIGHT_STANDBY_TIMEOUT))
            else:
                self._logger.debug("ESaver: Wake up at day")
                self._comps.display.set_brightness(self._settings.get_int(BRIGHTNESS))
                time.sleep(self._settings.get_int(DAY_STANDBY_TIMEOUT))
        else:
            if self.night_mode_active and (wake_time <= current_date_time < sleep_time):
                new_state = "Normal day mode"
                self._comps.display.set_brightness(self._settings.get_int(BRIGHTNESS))
                self._night_mode_active = False
            elif not self.night_mode_active and self._settings.get(MOTION_SENSOR_ENABLED):
                new_state = "Day standby mode"
                self._comps.display.set_brightness(STANDBY_BRIGHTNESS)
            if current_date_time <= wake_time or current_date_time >= sleep_time:
                new_state = "Night mode"
                self._night_mode_active = True
                self._comps.display.set_brightness(NIGHT_MODE_BRIGHTNESS)
            if self._previous_state != new_state:
                self._logger.debug("ESaver: %s", new_state)
                self._previous_state = new_state
