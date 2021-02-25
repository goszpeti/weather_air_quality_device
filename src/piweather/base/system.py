import os
import platform
import socket
import subprocess

import getrpimodel

from piweather.base.logger import Logger


class RuntimeSystem():
    """
    Singleton that abstracts information about the current system and provides a wrapper
    to generic RPi system functions, BUT only execute it on the RPi. 
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self._logger = Logger()
        self._is_target_system = False
        self._platform = platform.system()
        self._determine_if_target_system()

    def _determine_if_target_system(self):
        if self._platform != "Linux":
            return
        try:
            target_platform = getrpimodel.model()
            if target_platform:
                self._is_target_system = True
                self._platform = target_platform
                self._logger.info("System: Raspberry Pi %s detected", self._platform)
        except FileNotFoundError:
            self._logger.info("System: Non RPi-system detected.\n Current platform is: %s",
                              self._platform)

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

    def get_ip(self) -> ["ipv4", "ipv6"]:
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
        return [ipv4, ipv6]
