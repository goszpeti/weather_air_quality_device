from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from waqd.base.network import Network
from waqd.base.system import RuntimeSystem
from waqd.web.authentication import (
    User,
    get_current_user_with_exception,
)
from waqd.web.templates import base_template
from waqd.web.authentication import PermissionChecker, get_current_user_plain

rt = APIRouter()

current_path = Path(__file__).parent.resolve()

@rt.get("/", response_class=HTMLResponse)
async def menu(user: Annotated[User, Depends(get_current_user_plain)]):
    menu_content = ""
    local = False
    if user:
        local = PermissionChecker(
            required_permissions=[
                "users:local",
            ]
        ).check_permissions(user)
    menu_content = base_template(
        "views/menu.html",
        {
            "local": local,
            "logged_in": bool(user),
        },
        current_path,
    )
    return HTMLResponse(menu_content)

@rt.get("/network_icon", response_class=HTMLResponse)
async def wifi_signal_strength(
    current_user: Annotated[User, Depends(get_current_user_with_exception)],
):
    if not PermissionChecker(
        required_permissions=[
            "users:local",
        ]
    ).check_permissions(current_user):
        return HTMLResponse("Nope")
    network = Network()
    icon_name = "cloud_off"
    if network.is_connected_via_eth():
        icon_name = "lan"
    elif network.is_connected_via_wlan():
        strength = network.current_wifi_strength()
        if strength:
            if 75 < strength <= 100:
                icon_name = "wifi_full"
            elif strength > 50:
                icon_name = "wifi_2_bar"
            else:
                icon_name = "wifi_1_bar"
    image = f"""<svg viewBox="0 0 24 24" class="h-8">
    <use href="/static/general_icons/{icon_name}.svg#main" fill="white"/></svg>"""
    return HTMLResponse(image)


@rt.post("/shutdown", response_class=HTMLResponse)
async def shutdown(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    is_local = PermissionChecker(
        required_permissions=[
            "users:local",
        ]
    ).check_permissions(current_user)
    if is_local:
        RuntimeSystem().shutdown()
    return HTMLResponse("OK")


@rt.post("/restart", response_class=HTMLResponse)
async def restart(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    is_local = PermissionChecker(
        required_permissions=[
            "users:local",
        ]
    ).check_permissions(current_user)
    if is_local:
        RuntimeSystem().restart()
    return HTMLResponse("OK")
