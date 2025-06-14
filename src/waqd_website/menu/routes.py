from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from waqd.web.templates import base_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()

@rt.get("/", response_class=HTMLResponse)
async def menu():
    user = ""
    menu_content = base_template(
        "views/menu.html",
        {
            "logged_in": bool(user),
        },
        current_path,
    )
    return HTMLResponse(menu_content)
