from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from ..public.authentication import User, get_current_user_with_redirect

from ..templates import render_main, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/wifi", response_class=HTMLResponse)
async def network_mgr():
    content = sub_template(
        "wifi.html",
        {},
        current_path,
    )
    return content
