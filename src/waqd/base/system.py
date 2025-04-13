

import os
import platform


class RuntimeSystem():
    """
    Singleton that abstracts information about the current system and provides a wrapper
    to generic RPi system functions, BUT only execute it on the RPi.
    """
    _instance = None
    _is_target_system = False
    _platform = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self._platform = f"{platform.system()}@{platform.machine()}"
        self._determine_if_target_system()

    def _determine_if_target_system(self):
        # late import to be able to mock this
        from adafruit_platformdetect import Detector  # pylint: disable=import-outside-toplevel
        detector = Detector()
        # late init of logger, so on non target hosts the file won't be used already
        self._is_target_system = detector.board.any_raspberry_pi
        if self._is_target_system:
            self._platform = detector.board.id

    @property
    def platform(self) -> str:
        """ Return target platform (RPi version like Model B) or current platform name. """
        return str(self._platform).replace("_", " ")

    @property
    def is_target_system(self) -> bool:
        """ Return true, if it is the intended target system (currently only RPi) """
        return self._is_target_system

    def shutdown(self):
        """ Shuts down system, if it is the target system """
        if self._is_target_system:
            os.system("shutdown now")

    def restart(self):
        """ Restarts system, if it is the target system """
        if self._is_target_system:
            os.system("shutdown -r now")
