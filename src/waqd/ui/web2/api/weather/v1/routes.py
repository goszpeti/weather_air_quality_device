# ?field=tempunit=true
from fastapi import HTTPException, Request, APIRouter
from fastapi.responses import JSONResponse
from waqd.components.weather.base_types import Weather, DailyWeather
from .connector import WeatherRetrieval

rt = APIRouter()


@rt.get("/api/weather/v1/current", response_class=JSONResponse)
async def weather_current(request: Request) -> Weather:
    values = WeatherRetrieval().get_current_weather()
    if not values:
        raise HTTPException(status_code=404, detail='{"message": "No data available"}')
    return values


@rt.get("/api/weather/v1/5day-forecast", response_class=JSONResponse)
async def weather_forecast(request: Request) -> list[DailyWeather]:
    values = WeatherRetrieval().get_5_day_forecast()
    if not values:
        raise HTTPException(status_code=404, detail='{"message": "No data available"}')
    return values
