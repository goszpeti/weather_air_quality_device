from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from waqd.base.network import Network
from waqd.base.system import RuntimeSystem
from waqd.ui.web2.authentication import (
    User,
    get_current_user_with_exception,
)
from waqd.ui.web2.templates import render_main, sub_template
from ...authentication import PermissionChecker

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/", response_class=HTMLResponse)
async def network_mgr(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    if not PermissionChecker(
        required_permissions=[
            "users:local",
        ]
    ).check_permissions(current_user):
        return HTMLResponse("Nope")
    content = sub_template(
        "network_mgr.html",
        {},
        current_path,
    )
    return render_main(content, current_user)


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
async def wifi_list(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    content = sub_template(
        "wifi_list.html", {"wifi_networks": Network().list_wifi()}, current_path, True
    )
    return HTMLResponse(content)


@rt.post("/wifi/connect", response_class=HTMLResponse)
async def wifi_connect(
    current_user: Annotated[User, Depends(get_current_user_with_exception)],
    ssid: str = Form(),
    password: str = Form(),
):
    Network().connect_wifi(ssid, password)
    return HTMLResponse("OK")


@rt.post("/wifi/disconnect", response_class=HTMLResponse)
async def wifi_disconnect(
    current_user: Annotated[User, Depends(get_current_user_with_exception)], ssid: str = Form()
):
    Network().disconnect_wifi(ssid)
    return HTMLResponse("OK")
