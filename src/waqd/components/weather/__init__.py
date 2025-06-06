

from abc import ABC, abstractmethod

from waqd.base.component import Component
from .base_types import Weather, DailyWeather, WeatherQuality
from .open_weather import OpenWeatherMap
from .open_topo import OpenTopoData
from .open_meteo import OpenMeteo

class WeatherProvider(ABC, Component):

    @abstractmethod
    def get_current_weather(self) ->Weather | None:
        raise NotImplementedError

    @abstractmethod
    def get_5_day_forecast(self) -> list[DailyWeather]:
        raise NotImplementedError

__all__ = [
    "WeatherProvider",
    "Weather",
    "DailyWeather",
    "WeatherQuality",
    "OpenWeatherMap",
    "OpenTopoData",
    "OpenMeteo",
]