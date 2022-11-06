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


# Stop
# TODO add configuration
# https://github.com/balena-os/wifi-connect/blob/master/scripts/raspbian-install.sh

#sudo pkill wifi-connect

# # sudo systemctl start comitup

# /usr/local/share/wifi-connect/ui/static/media
# sudo systemctl stop comitup
# sudo systemctl stop NetworkManager

import socket
import subprocess
from typing import Callable, Tuple
from time import sleep
from waqd.base.logger import Logger
from waqd.base.system import RuntimeSystem
from waqd.base.signal import QtSignalRegistry


class Network():
    """
    Singleton that abstracts information about the network.
    """
    NW_READY_SIG_NAME = "network_ready_sig"
    _instance = None
    _internet_reconnect_try = 0  # internal counter for wlan restart
    _disable_network = False
    _wait_for_network_counter = 0
    _wait_for_internet_counter = 0
    internet_connected_once = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self._runtime_system = RuntimeSystem()
        self.wait_for_network()

    @property
    def internet_connected(self) -> bool:
        if self._disable_network:
            return False
        try:
            socket.create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        return False
    
    @property
    def network_connected(self) -> bool:
        [ipv4, ipv6] = self.get_ip()
        if not ipv4 and not ipv6 or self._disable_network:
            return False
        return True

    def get_ip(self) -> Tuple[str, str]:  # "ipv4", "ipv6"
        """ Gets IP 4 and 6 addresses on target system """
        ipv4 = ""
        ipv6 = ""
        if self._runtime_system.is_target_system:
            try:
                ret = subprocess.check_output("hostname -I", shell=True)
                ret_str = ret.decode("utf-8")
            except Exception as e:
                Logger().error("Network: Can't get IP address")
                return (ipv4, ipv6)
            # if both 4 and 6 are available, there is a space between them
            ips = ret_str.split(" ")
            for ip_adr in ips:
                if "." in ip_adr:
                    ipv4 = ip_adr
                elif ":" in ip_adr:
                    ipv6 = ip_adr
        else:
            ipv4 = socket.gethostbyname(socket.gethostname())
        if ipv4 in ["localhost", "127.0.0.1"]:  # we want the LAN address
            ipv4 = ""
        return (ipv4, ipv6)

    def register_network_notification(self, sig, cbk: Callable):
        QtSignalRegistry().register_callback(self.NW_READY_SIG_NAME, sig, cbk)
        
    # def deregister_network_notifications(self):
    #     self._network_cbks.clear()

    def check_internet_connection(self):
        """
        RPi fails often when WLAN conncetion is unstable.
        The restart of the adapter is black voodo magic, which is attempted after the second failure.
        If that doesn't help, the RPi reboots on the next failure.
        """
        if self.internet_connected_once:  # at least once connected:
            if self._internet_reconnect_try == 2:
                # TODO use py network manager
                # Logger().error("Watchdog: Restarting wlan...")
                # os.system("sudo systemctl restart dhcpcd")
                # sleep(2)
                # os.system("wpa_cli -i wlan0 reconfigure")
                # os.system("sudo dhclient")
                sleep(5)
            # failed 3 times straight - restart linux
            if self._internet_reconnect_try == 3:
                # TODO dialog!
                Logger().error("Network: Restarting system - Net failure...")
                self._runtime_system.restart()
        if not self.internet_connected:
            self._internet_reconnect_try += 1
            sleep(5)
        else:
            if self._internet_reconnect_try != 0:
                self._internet_reconnect_try = 0
                QtSignalRegistry().emit_sig_callback(self.NW_READY_SIG_NAME)

    def wait_for_network(self) -> bool:
        max_error = 5
        while not self.network_connected and self._wait_for_network_counter < max_error:
            sleep(1)
            self._wait_for_network_counter += 1
            if self._wait_for_network_counter == 0:
                Logger().info("Waiting for network...")

        self._wait_for_network_counter = 0
        if self._wait_for_network_counter == max_error:
            return False
        return True
    
    def wait_for_internet(self) -> bool:
        self.wait_for_network()
        max_error = 5
        while not self.internet_connected and self._wait_for_internet_counter < max_error:
            sleep(1)
            self._wait_for_internet_counter += 1
            if self._wait_for_internet_counter == 0:
                Logger().info("Waiting for network...")

        if self._wait_for_internet_counter == max_error:
            return False
        self._wait_for_internet_counter = 0
        return True
