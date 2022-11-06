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
