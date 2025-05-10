from pathlib import Path


from fastapi import Depends, FastAPI
import waqd.app as base_app
import waqd

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import RedirectResponse

from . import LOCAL_SERVER_PORT

from .public.authentication import get_current_user_with_redirect


from .api.sensor.v1.routes import rt as sensor_v1_router
from .api.weather.v1.routes import rt as weather_v1_router
from .weather_main.routes import rt as weather_router
from .settings.routes import rt as settings_router
from .public.routes import rt as public_router

current_path = Path(__file__).parent.resolve()

web_app = FastAPI(
    title="Waqd Web UI",
    description="Web UI for Waqd",
    version=waqd.__version__,
    debug=waqd.DEBUG_LEVEL > 0,
    dependencies=[Depends(get_current_user_with_redirect)],
)

web_app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        f"http://127.0.0.1:{LOCAL_SERVER_PORT}",
        f"http://localhost:{LOCAL_SERVER_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
web_app.mount("/static", StaticFiles(directory=str(waqd.assets_path)), name="static")

# HTML routers
web_app.include_router(weather_router, prefix="/weather")
web_app.include_router(settings_router, prefix="/settings")
web_app.include_router(public_router, prefix="/public")

# API routers
web_app.include_router(weather_v1_router, prefix="/api/weather/v1")
web_app.include_router(sensor_v1_router, prefix="/api/sensor/v1")


@web_app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/weather")


if base_app.comp_ctrl is None:
    base_app.basic_setup()
