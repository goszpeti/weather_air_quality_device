from pathlib import Path
from typing import Annotated
from urllib.parse import quote
from requests import get

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from ..public.authentication import User, get_current_user_with_redirect

from ..templates import render_main, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/", response_class=HTMLResponse)
async def settings(current_user: Annotated[User, Depends(get_current_user_with_redirect)]):
    content = sub_template(
        "settings.html",
        {},
        current_path,
    )
    return render_main(content, current_user)


@rt.get("/location_search_result", response_class=HTMLResponse)
async def location_search_result(query: str):
    # request to the Open-Meteo Geocoding API
    location_data = get(
        "https://geocoding-api.open-meteo.com/v1/search?name=" + quote(query)
    ).json()
    return sub_template(
        "location_result.html",
        {"location_data": location_data},
        current_path,  #
        component=True,
    )
