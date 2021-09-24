import logging

class Backlight():
    __shared_state = {}
    _brighntess = 50
    fade_duration = 1.0

    def __init__(self):
        self.__dict__ = self.__shared_state # use borg pattern
    
    @property
    def brightness(self):
        return self._brighntess
    
    @brightness.setter
    def brightness(self, value):
        self._brighntess = value
        logging.debug("Brightness set to %i", value)
