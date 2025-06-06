from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .connector import SensorRetrieval, SensorWriter
from .model import SensorApi_v1

rt = APIRouter()


@rt.get("/interior", response_class=JSONResponse)
async def get_interior(request: Request, units: bool = False) -> SensorApi_v1:
    values = SensorRetrieval().get_interior_sensor_values(units=units)
    return values


@rt.get("/exterior", response_class=JSONResponse)
async def get_exterior(request: Request, units: bool = False) -> SensorApi_v1:
    values = SensorRetrieval().get_exterior_sensor_values(units=units)
    return values

@rt.post("/interior", response_class=JSONResponse)
async def post_interior(request: Request, values: SensorApi_v1)
    SensorWriter().write_sensor_values(values)

@rt.post("/exterior", response_class=JSONResponse)
async def post_exterior(request: Request, values: SensorApi_v1)
    SensorWriter().write_sensor_values(values)
