from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..templates import render_spa, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    content = sub_template(
        "about.html",
        {},
        current_path,
    )
    return render_spa(request, content)


@rt.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    content = sub_template(
        "login.html",
        {},
        current_path,
    )
    return render_spa(request, content)


@rt.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    content = sub_template(
        "logout.html",
        {},
        current_path,
    )
    return render_spa(request, content)
