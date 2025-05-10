# ?field=tempunit=true
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from waqd.components.weather.base_types import DailyWeather, Weather

from .connector import WeatherRetrieval

rt = APIRouter()


@rt.get("/current", response_class=JSONResponse)
async def weather_current(request: Request) -> Weather:
    values = WeatherRetrieval().get_current_weather()
    if not values:
        raise HTTPException(status_code=404, detail='{"message": "No data available"}')
    return values


@rt.get("/5day-forecast", response_class=JSONResponse)
async def weather_forecast(request: Request) -> list[DailyWeather]:
    values = WeatherRetrieval().get_5_day_forecast()
    if not values:
        raise HTTPException(status_code=404, detail='{"message": "No data available"}')
    return values
