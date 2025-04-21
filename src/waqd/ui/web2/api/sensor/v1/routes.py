# ?field=tempunit=true
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from .connector import SensorRetrieval

rt = APIRouter()


@rt.get("/api/sensor/interior", response_class=JSONResponse)
async def interior_rt(request: Request, units: bool = False):
    values = SensorRetrieval()._get_interior_sensor_values(units=units)
    return values


@rt.get("/api/sensor/exterior", response_class=JSONResponse)
async def exterior_rt(request: Request, units: bool = False):
    values = SensorRetrieval()._get_exterior_sensor_values(units=units)
    return values
