from typing import Optional
from pydantic import BaseModel, Field


class ForecastView(BaseModel):
    temp: Optional[str] = Field(description="Temperature in Celsius", default="N/A")
    hum: Optional[str] = Field(description="Humidity in %", default="N/A")
    baro: Optional[str] = Field(description="Pressure in hPa", default="N/A")
    weather_icon: Optional[str] = Field(
        description="Weather icon", default="static/weather_icons/wi-cloud.svg"
    )
    weather_day_min_max: Optional[str] = Field(
        description="Day min/max temperature", default="N/A"
    )
    weather_night_min_max: Optional[str] = Field(
        description="Night min/max temperature", default="N/A"
    )


class ExteriorView(BaseModel):
    temp: Optional[str] = Field(description="Temperature in Celsius", default="N/A")
    hum: Optional[str] = Field(description="Humidity in %", default="N/A")
    baro: Optional[str] = Field(description="Pressure in hPa", default="N/A")
    weather_icon: Optional[str] = Field(
        description="Weather icon", default="static/weather_icons/wi-cloud.svg"
    )
    weather_day_min_max: Optional[str] = Field(
        description="Day min/max temperature", default="N/A"
    )
    weather_night_min_max: Optional[str] = Field(
        description="Night min/max temperature", default="N/A"
    )
