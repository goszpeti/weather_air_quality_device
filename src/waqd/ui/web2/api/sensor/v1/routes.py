# ?field=tempunit=true
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from .connector import SensorRetrieval
from .model import SensorApi_v1

rt = APIRouter()


@rt.get("/interior", response_class=JSONResponse)
async def interior_rt(request: Request, units: bool = False) -> SensorApi_v1:
    values = SensorRetrieval().get_interior_sensor_values(units=units)
    return values


@rt.get("/exterior", response_class=JSONResponse)
async def exterior_rt(request: Request, units: bool = False) -> SensorApi_v1:
    values = SensorRetrieval().get_exterior_sensor_values(units=units)
    return values
