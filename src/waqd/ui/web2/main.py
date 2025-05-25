import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import waqd
import waqd.app as base_app

from . import LOCAL_SERVER_PORT
from .api.sensor.v1.routes import rt as sensor_v1_router
from .api.weather.v1.routes import rt as weather_v1_router
from .authentication import get_current_user_with_exception, get_current_user_with_redirect
from .local.routes import rt as local_router
from .pages.public.routes import rt as public_router
from .pages.settings.routes import rt as settings_router
from .pages.weather_main.routes import rt as weather_router

current_path = Path(__file__).parent.resolve()

web_app = FastAPI(
    title="Waqd Web UI",
    description="Web UI for Waqd",
    version=waqd.__version__,
    debug=waqd.DEBUG_LEVEL > 0,
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


@web_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# Static files
web_app.mount("/static", StaticFiles(directory=str(waqd.assets_path)), name="static")

# HTML routers
web_app.include_router(
    weather_router,
    prefix="/weather",
)
web_app.include_router(
    settings_router,
    prefix="/settings",
    dependencies=[Depends(get_current_user_with_redirect)],
)
web_app.include_router(
    local_router,
    prefix="/local",
    dependencies=[Depends(get_current_user_with_redirect)],
)
web_app.include_router(public_router, prefix="/public")

from starlette.exceptions import HTTPException as StarletteHTTPException


class RequiresLoginException(StarletteHTTPException):
    pass


@web_app.exception_handler(RequiresLoginException)
async def exception_handler(request, exc):
    return RedirectResponse(url="/public/login")


# API routers
web_app.include_router(
    weather_v1_router,
    prefix="/api/weather/v1",
    dependencies=[Depends(get_current_user_with_exception)],
)
web_app.include_router(
    sensor_v1_router,
    prefix="/api/sensor/v1",
    dependencies=[Depends(get_current_user_with_exception)],
)


@web_app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/weather")


if base_app.comp_ctrl is None:
    base_app.basic_setup()
