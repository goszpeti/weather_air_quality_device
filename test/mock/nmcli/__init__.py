
from typing import Optional
from attr import dataclass



class RadioMgr():
    _state = True

    def wifi_on(self):
        self._state = True

    def wifi_off(self):
        self._state = False
    
    def wifi(self):
        return self._state

radio = RadioMgr()
@dataclass(frozen=True)
class Device:
    device: str
    device_type: str
    state: str
    connection: Optional[str]

@dataclass(frozen=True)
class DeviceWifi:
    in_use: bool
    ssid: str
    bssid: str
    mode: str
    chan: int
    freq: int
    rate: int
    signal: int
    security: str

class DeviceMgr():
    _eth = True

    @staticmethod
    def wifi():
        if radio.wifi():
            return [
                    DeviceWifi(in_use=True, ssid='WLAN-B.A', bssid='1', mode='Infra', chan=6, freq=2437, rate=260, signal=89, security='WPA2 WPA3'), 
                    DeviceWifi(in_use=False, ssid='WLAN-B.A', bssid='2', mode='Infra', chan=52, freq=5260, rate=540, signal=64, security='WPA2 WPA3'),
                    DeviceWifi(in_use=False, ssid='WLAN-985340', bssid='3', mode='Infra', chan=11, freq=2462, rate=540, signal=67, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='WLAN-206656', bssid='4', mode='Infra', chan=11, freq=2462, rate=130, signal=59, security='WPA2'),
                    DeviceWifi(in_use=False, ssid='WLAN-130251', bssid='5', mode='Infra', chan=1, freq=2412, rate=540, signal=50, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='WLAN-426465', bssid='6', mode='Infra', chan=6, freq=2437, rate=540, signal=50, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='FRITZ!Box 7590 EJ', bssid='7', mode='Infra', chan=13, freq=2472, rate=260, signal=39, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='FRITZ!Box 7590 EJ', bssid='8', mode='Infra', chan=44, freq=5220, rate=540, signal=35, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='', bssid='9', mode='Infra', chan=104, freq=5520, rate=540, signal=27, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='', bssid='10', mode='Infra', chan=104, freq=5520, rate=540, signal=24, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='FRITZ!Box 6660 Cable IV', bssid='11', mode='Infra', chan=36, freq=5180, rate=270, signal=22, security='WPA2'), 
                    DeviceWifi(in_use=False, ssid='FRITZ!Box 7530 HB', bssid='12', mode='Infra', chan=36, freq=5180, rate=270, signal=20, security='WPA2')
                    ]
        else:
            return []

    def status(self):
        if self._eth:
            self._eth = False
            eth_status = "connected"
        else:
            self._eth = True
            eth_status = "disconnected"
        status=  [
            Device(
                device="eth0",
                device_type="ethernet",
                state=eth_status,
                connection="Wired connection 1",
            ),
            Device(
                device="lo",
                device_type="loopback",
                state="connected",
                connection="(externally)  lo",
            ),
            Device(
                device="docker0",
                device_type="bridge",
                state="connected",
                connection="(externally)  docker0",
            ),
        ]
        if radio.wifi():
            status.append(Device(device="wlan0", device_type="wifi", state="connected", connection="HomeNet")),
            status.append(Device(
                device="p2p-dev-wlan0",
                device_type="wifi-p2p",
                state="disconnected",
                connection=None,
            ),)
        return status

    def wifi_connect(self, ssid, password):
        return True
    
    def disconnect(self, ssid):
        return True


device = DeviceMgr()
