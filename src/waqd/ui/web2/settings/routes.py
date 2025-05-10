from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ..public.authentication import User, get_current_user_with_redirect

from ..templates import render_spa, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/", response_class=HTMLResponse)
async def settings(current_user: Annotated[User, Depends(get_current_user_with_redirect)]):
    content = sub_template(
        "settings.html",
        {},
        current_path,
    )
    return render_spa(content, current_user)
