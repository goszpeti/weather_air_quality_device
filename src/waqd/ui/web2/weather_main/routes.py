from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from waqd.ui.web2.api.sensor.v1.model import SensorApi_v1
from waqd.ui.web2.weather_main.model import ExteriorView, ForecastView

from ..templates import render_spa, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/weather", response_class=HTMLResponse)
async def root(request: Request):
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
                    "background": "static/weather_bgrs/cloudy_night_bg.jpg",
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
    return render_spa(request, content)


@rt.get("/weather/interior", response_class=JSONResponse)
async def interior(request: Request):
    return RedirectResponse(url="/api/sensor/interior?units=True")


@rt.get("/weather/exterior", response_class=JSONResponse)
async def exterior(request: Request) -> ExteriorView:
    return ExteriorView(
        temp="N/A",
        hum="N/A",
        baro="N/A",
        weather_icon="static/weather_icons/wi-cloud.svg",
        weather_day_min_max="N/A",
        weather_night_min_max="N/A",
    )


@rt.get("/weather/forecast", response_class=JSONResponse)
async def forecast(request: Request) -> ForecastView:
    return ForecastView(
        temp="N/A",
        hum="N/A",
        baro="N/A",
        weather_icon="static/weather_icons/wi-cloud.svg",
        weather_day_min_max="N/A",
        weather_night_min_max="N/A",
    )
