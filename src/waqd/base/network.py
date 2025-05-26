import socket
import subprocess
from typing import Tuple
from time import sleep

import nmcli
from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem

class Network:
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
        self._devices = nmcli.device.status()
        self._wifi_networks = nmcli.device.wifi()

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
        """Gets IP 4 and 6 addresses on target system"""
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

    def check_internet_connection(self):
        """
        RPi fails often when WLAN conncetion is unstable.
        The restart of the adapter is black voodo magic, which is attempted after the second failure.
        If that doesn't help, the RPi reboots on the next failure.
        """
        self._devices = nmcli.device.status()
        self._wifi_networks = nmcli.device.wifi()
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
                # TODO emit signal

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
    
    def is_connected_via_eth(self) -> bool:
        for device in self._devices:
            if device.device_type == "ethernet" and device.state == "connected":
                return True
        return False

    def is_connected_via_wlan(self) -> bool:
        for device in self._devices:
            if device.device_type == "wifi" and device.state == "connected":
                return True
        return False
    
    def list_wifi(self, include_hidden=False):
        # filter out duplicates
        wifi_networks = {}
        for device in self._wifi_networks:
            if not device.ssid:
                if not include_hidden:
                    continue
            same_device = wifi_networks.get(device.ssid, "")
            if same_device and device.in_use == same_device.in_use:
                continue
            wifi_networks[device.ssid] = device
        return wifi_networks

    def current_wifi_strength(self) -> int|None:
        for device in self._wifi_networks:
            if device.in_use:
                return device.signal
        return None
    def connect_wifi(self, ssid: str, password: str):
        pass

    def disconnect_wifi(self, ssid: str):
        pass

    def enable_wifi(self):
        pass

    def disable_wifi(self):
        pass