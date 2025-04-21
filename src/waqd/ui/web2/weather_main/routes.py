from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from ..templates import render_spa
from ..api.sensor.v1.connector import SensorRetrieval
from ..templates import simple_template

rt = APIRouter()

@rt.get("/weather", response_class=HTMLResponse)
async def root(request: Request):
    content = interior_card()
    content = simple_template("weather_main/waqd.html", {"interior_card": content})
    return render_spa(request, content)


def interior_card():
    values = SensorRetrieval()._get_interior_sensor_values(units=True)
    return simple_template("weather_main/components/interior_card.html", {})
