from functools import partial
from pathlib import Path
import waqd.app as base_app
import waqd

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse


from .api.sensor.v1.routes import rt as sensor_v1_router
from .weather_main.routes import rt as weather_router

current_path = Path(__file__).parent.resolve()

web_app = FastAPI(
    title="Waqd Web UI",
    description="Web UI for Waqd",
    version=waqd.__version__,
    debug=waqd.DEBUG_LEVEL > 0,
    # openapi_url=None,
)
web_app.mount("/static", StaticFiles(directory=str(waqd.assets_path)), name="static")
web_app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
web_app.include_router(sensor_v1_router)
web_app.include_router(weather_router)


@web_app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/weather")

if base_app.comp_ctrl is None:
    base_app.basic_setup()
