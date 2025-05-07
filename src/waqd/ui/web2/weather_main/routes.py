import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import waqd.app as base_app
from waqd.assets.assets import get_asset_file_relative
from waqd.ui import get_localized_date
from waqd.ui.web2.api.sensor.v1.connector import SensorRetrieval
from waqd.ui.web2.api.weather.v1.connector import WeatherRetrieval
from ..public.authentication import (
    User,
    get_current_user_redirect,
)
from waqd.ui.web2.weather_main.model import ExteriorView, ForecastView

from ..templates import render_spa, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


# admin: bool = Depends(
#     PermissionChecker(
#         required_permissions=[
#             "users:admin",
#         ]
#     )
# ),
@rt.get("/weather", response_class=HTMLResponse)
async def root(
    request: Request, current_user: Annotated[User, Depends(get_current_user_redirect)]
):
    interior = sub_template("interior.html", {}, current_path, True)
    exterior = sub_template("exterior.html", {}, current_path, True)
    forecast = sub_template("forecast.html", {}, current_path, True)
    content = sub_template(
        "waqd.html",
        {
            "cards": [
                {
                    "name": "Interior",
                    "background": "static/gui_bgrs/background_interior2.jpg",
                    "content": interior,
                    "endpoint": "/weather/interior",
                },
                {
                    "name": "Exterior",
                    "background": "",
                    "content": exterior,
                    "endpoint": "/weather/exterior",
                },
                {
                    "name": "Forecast",
                    "background": "static/gui_bgrs/background_s7.jpg",
                    "content": forecast,
                    "endpoint": "/weather/forecast",
                },
            ]
        },
        current_path,
    )
    return render_spa(content, overflow=False)


@rt.get("/weather/interior", response_class=JSONResponse)
async def interior(request: Request):
    return RedirectResponse(url="/api/sensor/v1/interior?units=True")


@rt.get("/weather/exterior", response_class=JSONResponse)
async def exterior(request: Request) -> ExteriorView:
    ext_values = SensorRetrieval().get_exterior_sensor_values(units=True)
    current_weather = WeatherRetrieval().get_current_weather()
    # TODO: add None handling
    forecast = WeatherRetrieval().get_5_day_forecast()
    weather_bgr = get_asset_file_relative(current_weather.get_background_image())
    return ExteriorView(
        background=weather_bgr,
        temp=ext_values.temp,
        hum=ext_values.hum,
        weather_icon=get_asset_file_relative(current_weather.get_icon()),
        weather_day_min_max=f"{forecast[0].temp_min}°/{forecast[0].temp_max}°",
        weather_night_min_max=f"{forecast[0].temp_night_min}°/{forecast[0].temp_night_max}°",
    )


@rt.get("/weather/forecast", response_class=JSONResponse)
async def forecast(request: Request) -> ForecastView:
    forecast = WeatherRetrieval().get_5_day_forecast()
    current_date_time = datetime.datetime.now()

    return ForecastView(
        day_1_label=get_localized_date(
            current_date_time + datetime.timedelta(days=1), base_app.settings
        ),
        day_1_weather_icon=get_asset_file_relative(forecast[0].get_icon()),
        day_1_weather_day_min_max=f"{forecast[0].temp_min}°/{forecast[0].temp_max}°",
        day_1_weather_night_min_max=f"{forecast[0].temp_night_min}°/{forecast[0].temp_night_max}°",
        day_2_label=get_localized_date(
            current_date_time + datetime.timedelta(days=2), base_app.settings
        ),
        day_2_weather_icon=get_asset_file_relative(forecast[1].get_icon()),
        day_2_weather_day_min_max=f"{forecast[1].temp_min}°/{forecast[1].temp_max}°",
        day_2_weather_night_min_max=f"{forecast[1].temp_night_min}°/{forecast[1].temp_night_max}°",
        day_3_label=get_localized_date(
            current_date_time + datetime.timedelta(days=3), base_app.settings
        ),
        day_3_weather_icon=get_asset_file_relative(forecast[2].get_icon()),
        day_3_weather_day_min_max=f"{forecast[2].temp_min}°/{forecast[2].temp_max}°",
        day_3_weather_night_min_max=f"{forecast[2].temp_night_min}°/{forecast[2].temp_night_max}°",
    )
