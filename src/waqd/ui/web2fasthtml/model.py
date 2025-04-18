from typing import NotRequired, TypedDict


class SensorApi_0_1(TypedDict):
    api_ver: str
    temp: NotRequired[str]  # deg C
    hum: NotRequired[str]  # %
    baro: NotRequired[str]  # hPa
    co2: NotRequired[str]  # ppm
    tvoc: NotRequired[str]  # ppb
    dust: NotRequired[str]  # ug per m3
    light: NotRequired[str]  # lux