from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import waqd
from waqd.web.templates import render_main, sub_template
from .menu.routes import rt as menu_router

current_path = Path(__file__).parent.resolve()

web_app = FastAPI(
    title="WAQD",
    description="WAQD website",
)

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "https://waqd.de",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

web_app.mount("/static", StaticFiles(directory=str(waqd.assets_path)), name="static")


@web_app.get("/", response_class=HTMLResponse)
async def root():
    index = sub_template("landing.html", {}, current_path)
    return render_main(index, None, overflow=True, root_path=current_path)

web_app.include_router(menu_router, prefix="/menu")
