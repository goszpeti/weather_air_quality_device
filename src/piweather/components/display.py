import os

from piweather.base.components import Component
from piweather.settings import (Settings,
                                BRIGHTNESS, DISP_TYPE_RPI, DISP_TYPE_WAVESHARE, DISPLAY_TYPE,
                                WAVESHARE_DISP_BRIGHTNESS_PIN)


class Display(Component):
    """
    Abstracts brightness handling for different display types.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings=settings)
        self._brightness = None
        self._reload_forbidden = True  # re-init flickers screen

        if (self._settings.get(DISPLAY_TYPE) == DISP_TYPE_WAVESHARE and
                self._runtime_system.is_target_system):
            # to set brightness, this display needs to be hacked and is switched off by default.
            pin = self._settings.get(WAVESHARE_DISP_BRIGHTNESS_PIN)
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
        if self._brightness == brightness:
            return  # nothing to do
        try:
            disp_type = self._settings.get(DISPLAY_TYPE)
            if self._runtime_system.is_target_system:
                if disp_type == DISP_TYPE_WAVESHARE:
                    pwm_val = brightness * 10  # actually 1023 is max
                    pin = self._settings.get(WAVESHARE_DISP_BRIGHTNESS_PIN)
                    os.system("gpio -g pwm " + str(pin) + " " + str(pwm_val))
                elif disp_type == DISP_TYPE_RPI:
                    from rpi_backlight import Backlight  # pylint: disable=import-outside-toplevel
                    backlight = Backlight() # TODO don't instantiate every time
                    backlight.fade_duration = 0.5
                    backlight.brightness = brightness
                else:
                    os.system("vcgencmd display_power 0")
            # save set value
            self._brightness = brightness
        except Exception as error:
            self._logger.error(
                "Display: Cannot set display brightness to %i: %s", brightness, str(error))
