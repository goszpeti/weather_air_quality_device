from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..templates import render_spa, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    # interior = sub_template("interior.html", {}, current_path, True)
    # exterior = sub_template("exterior.html", {}, current_path, True)
    # forecast = sub_template("forecast.html", {}, current_path, True)
    content = sub_template(
        "settings.html",
        {},
        current_path,
    )
    return render_spa(content)
