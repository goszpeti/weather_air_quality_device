from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from waqd.web.authentication import (
    User,
    user_plain_check
)
from waqd.web.templates import base_template
from waqd.web.authentication import PermissionChecker

rt = APIRouter()

current_path = Path(__file__).parent.resolve()

@rt.get("/", response_class=HTMLResponse)
async def menu(user: Annotated[User, user_plain_check]):
    menu_content = ""
    menu_content = base_template(
        "views/menu.html",
        {
            "logged_in": bool(user),
        },
        current_path,
    )
    return HTMLResponse(menu_content)
