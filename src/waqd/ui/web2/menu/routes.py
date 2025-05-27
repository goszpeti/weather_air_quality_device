from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from waqd.base.network import Network
from waqd.base.system import RuntimeSystem
from waqd.ui.web2.authentication import (
    User,
    get_current_user_with_exception,
)
from waqd.ui.web2.templates import sub_template
from ..authentication import PermissionChecker

rt = APIRouter()

current_path = Path(__file__).parent.resolve()

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



@rt.post("/toggle_wifi", response_class=HTMLResponse)
async def toggle_wifi(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    if not PermissionChecker(
        required_permissions=[
            "users:local",
        ]
    ).check_permissions(current_user):
        return HTMLResponse("Nope")
    network = Network()
    if network.wifi_enabled():
        network.disable_wifi()
        return HTMLResponse("Turn On Wifi")
    else:
        network.enable_wifi()
        return HTMLResponse("Turn Off Wifi")

@rt.get("/ethernet_status", response_class=HTMLResponse)
async def ethernet_status(
    current_user: Annotated[User, Depends(get_current_user_with_exception)],
):
    if Network().is_connected_via_eth():
        content = "Connected"
    else:
        content = "Disconnected"
    return HTMLResponse(content)

@rt.get("/wifi_list", response_class=HTMLResponse)
async def network_mgr(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    content = sub_template(
        "snippets/wifi_list.html", {"wifi_networks": Network().list_wifi()}, current_path, True
    )
    return HTMLResponse(content)

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