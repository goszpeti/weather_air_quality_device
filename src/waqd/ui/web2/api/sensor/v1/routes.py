

# ?field=tempunit=true
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
from .connector import SensorRetrieval

rt = APIRouter()


@rt.get("/api/sensor/interior", response_class=JSONResponse)
async def interior_rt(request: Request, field:str|None=None, units:bool=False):
    values = SensorRetrieval()._get_interior_sensor_values(units=units)
    return values