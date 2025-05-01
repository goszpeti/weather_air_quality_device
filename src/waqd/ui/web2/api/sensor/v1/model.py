from typing import Optional
from pydantic import BaseModel, Field


class SensorApi_v1(BaseModel):
    api_ver: str = "1.0"
    temp: Optional[str] = Field(description="Temperature in Celsius", default="N/A")
    hum: Optional[str] = Field(description="Humidity in %", default="N/A")
    baro: Optional[str] = Field(description="Pressure in hPa", default="N/A")
    co2: Optional[str] = Field(description="CO2 in ppm", default="N/A")
    tvoc: Optional[str] = Field(description="TVOC in ppb", default="N/A")
    dust: Optional[str] = Field(description="Dust in µg/m³", default="N/A")
    light: Optional[str] = Field(description="Light in lux", default="N/A")
