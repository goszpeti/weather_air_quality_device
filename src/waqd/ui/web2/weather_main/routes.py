from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

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
                    "endpoint": "/api/sensor/interior?units=True",
                },
                {
                    "name": "Exterior",
                    "background": "static/weather_bgrs/cloudy_night_bg.jpg",
                    "content": exterior,
                    "endpoint": "/api/sensor/exterior?units=True",
                },
                {
                    "name": "Forecast",
                    "background": "static/gui_bgrs/background_s7.jpg",
                    "content": forecast,
                    "endpoint": "/api/sensor/exterior?units=True",
                },
            ]
        },
        current_path,
    )
    return render_spa(request, content)
