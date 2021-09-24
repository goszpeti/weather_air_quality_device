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
import os
import threading

from rpi_backlight import Backlight

from waqd.base.components import Component
from waqd.settings import (Settings,
                                BRIGHTNESS, DISP_TYPE_RPI, DISP_TYPE_WAVESHARE_5_LCD, DISPLAY_TYPE,
                                WAVESHARE_DISP_BRIGHTNESS_PIN)


class Display(Component):
    """
    Abstracts brightness handling for different display types.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings=settings)
        self._brightness = 0
        self._reload_forbidden = True  # re-init flickers screen

        if (self._settings.get(DISPLAY_TYPE) == DISP_TYPE_WAVESHARE_5_LCD and
                self._runtime_system.is_target_system):
            # to set brightness, this display needs to be hacked and is switched off by default.
            pin = self._settings.get_int(WAVESHARE_DISP_BRIGHTNESS_PIN)
            # use compiled gpio because with python it flickers
            os.system("gpio -g mode " + str(pin) + " pwm")
            os.system("gpio pwmc 1000")
            os.system("gpio pwmr 1000")
        # set configured brightness at startup
        self.set_brightness(self._settings.get(BRIGHTNESS))

    def get_brightness(self) -> int:
        """ Returns the current display brightness in percent, e.g. 75"""
        return self._brightness

    def set_brightness(self, brightness: int):
        """ Sets the current display brightness in percent, e.g. 75"""
        # TODO do this in a thread`? Can take too long for a bar

        if self._brightness == brightness:
            return  # nothing to do
        self._logger.debug("Setting brightness to %i", brightness)
        brightness_thread = threading.Thread(name="SetBrightness", target=self._set_brightness, args=[brightness, ])
        brightness_thread.start()

    def _set_brightness(self, brightness):
        try:
            disp_type = self._settings.get(DISPLAY_TYPE)
            if self._runtime_system.is_target_system:
                if disp_type == DISP_TYPE_WAVESHARE_5_LCD:
                    pwm_val = brightness * 10  # actually 1023 is max
                    pin = self._settings.get(WAVESHARE_DISP_BRIGHTNESS_PIN)
                    os.system("gpio -g pwm " + str(pin) + " " + str(pwm_val))
                elif disp_type == DISP_TYPE_RPI:
                    backlight = Backlight()
                    backlight.fade_duration = 0.5
                    backlight.brightness = brightness
                else:
                    os.system("vcgencmd display_power 0")
            # save set value
            self._brightness = brightness
        except Exception as error:
            self._logger.error(
                "Display: Cannot set display brightness to %i: %s", brightness, str(error))
