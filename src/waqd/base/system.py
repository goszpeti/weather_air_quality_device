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
import socket
import subprocess
from typing import Tuple
from time import sleep

from waqd.base.logger import Logger


class RuntimeSystem():
    """
    Singleton that abstracts information about the current system and provides a wrapper
    to generic RPi system functions, BUT only execute it on the RPi.
    """
    _instance = None
    _is_target_system = False
    _platform = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self._platform = platform.system()
        self._determine_if_target_system()

    def _determine_if_target_system(self):
        # late import to be able to mock this
        from adafruit_platformdetect import Detector
        detector = Detector()
        # late init of logger, so on non target hosts the file won't be used already
        self._is_target_system = detector.board.any_raspberry_pi
        self._platform = detector.board.id


    @property
    def platform(self) -> str:
        """ Return target platform (RPi version like Model B) or current platform name. """
        return self._platform

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

    def get_ip(self) -> Tuple["ipv4", "ipv6"]:
        """ Gets IP 4 and 6 addresses on target system """
        ipv4 = None
        ipv6 = None
        if self._is_target_system:
            ret = subprocess.check_output("hostname -I", shell=True)
            ret_str = ret.decode("utf-8")
            # if both 4 and 6 are available, there is a space between them
            ips = ret_str.split(" ")
            for ip_adr in ips:
                if "." in ip_adr:
                    ipv4 = ip_adr
                elif ":" in ip_adr:
                    ipv6 = ip_adr
        else:
            ipv4 = socket.gethostbyname(socket.gethostname())
        return (ipv4, ipv6)

    def wait_for_network(self):
        [ipv4, ipv6] = self.get_ip()

        i = 0
        while (not ipv4 and not ipv6) and i < 6:
            Logger().info("Waiting for network")
            sleep(0.5)
            [ipv4, ipv6] = self.get_ip()
            i += 1
