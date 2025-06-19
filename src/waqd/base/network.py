import re
from time import sleep

import nmcli
from nmcli import NetworkConnectivity
from waqd.base.file_logger import Logger
from waqd.base.system import RuntimeSystem


class Network:
    """
    Singleton that abstracts information about the network.
    """

    _instance = None
    _internet_reconnect_try = 0  # internal counter for wlan restart
    _disable_network = False
    _netw_counter = 0
    _inet_counter = 0
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
        self._eth_device = ""
        self._wlan_device = ""

        self.is_connected_via_eth()  # init _eth_device
        self.is_connected_via_wlan()  # init _wlan_device

        self.wait_for_network()

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
                if not self.is_connected_via_eth() and self.is_connected_via_wlan():
                    Logger().error("Network: Restarting wlan - Net failure...")
                    self.restart_wlan()
                sleep(5)
            # failed 3 times straight - restart linux
            if self._internet_reconnect_try == 3:
                # TODO dialog!
                Logger().error("Network: Restarting system - Net failure...")
                self._runtime_system.restart()
        if not self.get_connectivity() == NetworkConnectivity.FULL:
            self._internet_reconnect_try += 1
            sleep(5)
        else:
            if self._internet_reconnect_try != 0:
                self._internet_reconnect_try = 0
                # TODO emit signal

    def wait_for_network(self) -> bool:
        max_error = 5
        while (
            self.get_connectivity()
            not in [NetworkConnectivity.LIMITED, NetworkConnectivity.FULL]
            and self._netw_counter < max_error
        ):
            sleep(1)
            self._netw_counter += 1
            if self._netw_counter == 0:
                Logger().info("Waiting for network...")

        self._netw_counter = 0
        if self._netw_counter == max_error:
            return False
        return True

    def wait_for_internet(self) -> bool:
        self.wait_for_network()
        max_error = 5
        while (
            not self.get_connectivity() == NetworkConnectivity.FULL
            and self._inet_counter < max_error
        ):
            sleep(1)
            self._inet_counter += 1
            if self._inet_counter == 0:
                Logger().info("Waiting for network...")

        if self._inet_counter == max_error:
            return False
        self._inet_counter = 0
        return True

    def is_connected_via_eth(self) -> bool:
        for device in self._devices:
            if device.device_type == "ethernet" and device.state == "connected":
                self._eth_device = device.device
                return True
        return False

    def is_connected_via_wlan(self) -> bool:
        for device in self._devices:
            if device.device_type == "wifi" and device.state == "connected":
                self._wlan_device = device.device
                return True
        return False

    def list_wifi(self, include_hidden=False):
        # filter out duplicates
        self._wifi_networks = nmcli.device.wifi()
        wifi_networks = {}
        for device in self._wifi_networks:
            if not device.ssid:
                if not include_hidden:
                    continue
            same_device = wifi_networks.get(device.ssid, "")
            if same_device and same_device.in_use:
                continue
            wifi_networks[device.ssid] = device
        return wifi_networks

    def current_wifi_strength(self) -> int | None:
        for device in self._wifi_networks:
            if device.in_use:
                return device.signal
        return None

    def connect_wifi(self, ssid: str, password: str):
        Logger().info("Network: Connecting to WiFi: %s", ssid)
        nmcli.device.wifi_connect(ssid, password)

    def try_connect_wifi(self, ssid: str):
        cmd = ["device", "wifi", "connect", ssid]
        r = nmcli._syscmd.nmcli(cmd)
        m = re.search(r"Connection activation failed:", r)
        if m:
            raise nmcli.ConnectionActivateFailedException("Connection activation failed")

    def disconnect_wifi(self):
        Logger().info("Network: Disconnecting from WiFi")
        if self.is_connected_via_wlan():
            nmcli.device.disconnect(self._wlan_device)

    def enable_wifi(self):
        Logger().info("Network: Enabling WiFi")
        nmcli.radio.wifi_on()

    def disable_wifi(self):
        Logger().info("Network: Disabling WiFi")
        nmcli.radio.wifi_off()

    def wifi_enabled(self):
        return nmcli.radio.wifi()

    def get_connectivity(self) -> NetworkConnectivity:
        if (status := nmcli.networking.connectivity(check=True)) == NetworkConnectivity.FULL:
            self.internet_connected_once = True
        return status

    def restart_wlan(self):
        self.disable_wifi()
        sleep(2)
        self.enable_wifi()  # reconnects
