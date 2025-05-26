
from typing import Optional
from attr import dataclass


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
    @staticmethod
    def wifi():
        return [DeviceWifi(in_use=False, ssid='HomeNet', bssid='DC:39:6F:17:BB:50', mode='Infra', chan=6, freq=2437, rate=130, signal=100, security='WPA2'), 
                DeviceWifi(in_use=True, ssid='HomeNet', bssid='DC:39:6F:17:BB:51', mode='Infra', chan=116, freq=5580, rate=270, signal=92, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='WLAN-A.E', bssid='B0:FC:88:90:CD:64', mode='Infra', chan=6, freq=2437, rate=260, signal=89, security='WPA2 WPA3'), 
                DeviceWifi(in_use=False, ssid='WLAN-A.E', bssid='B0:FC:88:90:CD:63', mode='Infra', chan=52, freq=5260, rate=540, signal=64, security='WPA2 WPA3'),
                DeviceWifi(in_use=False, ssid='Artukovic', bssid='98:9B:CB:12:7C:59', mode='Infra', chan=6, freq=2437, rate=130, signal=72, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='WLAN-985340', bssid='04:A2:22:2E:8B:8A', mode='Infra', chan=11, freq=2462, rate=540, signal=67, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='Gaming-759F32', bssid='AE:FC:88:90:CD:63', mode='Infra', chan=52, freq=5260, rate=540, signal=64, security='WPA2 WPA3'), 
                DeviceWifi(in_use=False, ssid='WLAN-206656', bssid='D4:21:22:B2:89:D3', mode='Infra', chan=11, freq=2462, rate=130, signal=59, security='WPA2'),
                DeviceWifi(in_use=False, ssid='WLAN-130251', bssid='4C:1B:86:88:36:AB', mode='Infra', chan=1, freq=2412, rate=540, signal=50, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='WLAN-426465', bssid='F0:86:20:1E:FF:0E', mode='Infra', chan=6, freq=2437, rate=540, signal=50, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='', bssid='06:A2:22:2E:8B:89', mode='Infra', chan=36, freq=5180, rate=540, signal=44, security='WPA2'),
                DeviceWifi(in_use=False, ssid='Artukovic', bssid='98:9B:CB:12:7C:5A', mode='Infra', chan=36, freq=5180, rate=270, signal=40, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='FRITZ!Box 7590 EJ', bssid='3C:A6:2F:F7:A7:29', mode='Infra', chan=13, freq=2472, rate=260, signal=39, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='FRITZ!Box 7590 EJ', bssid='3C:A6:2F:F7:A7:2A', mode='Infra', chan=44, freq=5220, rate=540, signal=35, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='', bssid='F2:86:20:1E:FF:0C', mode='Infra', chan=104, freq=5520, rate=540, signal=27, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='', bssid='F2:86:20:1E:FF:0D', mode='Infra', chan=104, freq=5520, rate=540, signal=27, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='', bssid='F2:86:20:1E:FF:0A', mode='Infra', chan=104, freq=5520, rate=540, signal=24, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='', bssid='F2:86:20:1E:FF:0B', mode='Infra', chan=104, freq=5520, rate=540, signal=24, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='FRITZ!Box 6660 Cable IV', bssid='04:B4:FE:DF:35:67', mode='Infra', chan=36, freq=5180, rate=270, signal=22, security='WPA2'), 
                DeviceWifi(in_use=False, ssid='FRITZ!Box 7530 HB', bssid='74:42:7F:09:28:52', mode='Infra', chan=36, freq=5180, rate=270, signal=20, security='WPA2')]

    @staticmethod
    def status():
        return [
            Device(
                device="eth0",
                device_type="ethernet",
                state="disconnected",
                connection="Wired connection 1",
            ),
            Device(device="wlan0", device_type="wifi", state="connected", connection="HomeNet"),
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
            Device(
                device="p2p-dev-wlan0",
                device_type="wifi-p2p",
                state="disconnected",
                connection=None,
            ),
        ]

device = DeviceMgr()
