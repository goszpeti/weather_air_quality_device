from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from waqd.base.network import Network
from waqd.web.authentication import (
    User,
)
from waqd.web.templates import render_main, sub_template
from waqd.web.authentication import user_exception_check

rt = APIRouter()

current_path = Path(__file__).parent.resolve()

@rt.get("/", response_class=HTMLResponse)
async def network_mgr(current_user: Annotated[User, user_exception_check]):
    network = Network()
    if network.wifi_enabled():
        snippet = "turn_off_wifi.html"
    else:
        snippet = "turn_on_wifi.html"
    wifi_status_content = sub_template("snippets/" + snippet, {}, current_path, True)

    content = sub_template(
        "network_mgr.html",
        {"wifi_status": wifi_status_content},
        current_path,
    )
    return render_main(content, current_user)


@rt.post("/wifi/toggle", response_class=HTMLResponse)
async def toggle_wifi():
    network = Network()
    if network.wifi_enabled():
        network.disable_wifi()
        snippet = "turn_on_wifi.html"
    else:
        network.enable_wifi()
        snippet = "turn_off_wifi.html"
    return HTMLResponse(sub_template("snippets/" + snippet, {}, current_path, True))


@rt.get("/ethernet_status", response_class=HTMLResponse)
async def ethernet_status():
    if Network().is_connected_via_eth():
        content = "Connected"
    else:
        content = "Disconnected"
    return HTMLResponse(content)


@rt.get("/wifi_list", response_class=HTMLResponse)
async def wifi_list():
    content = sub_template(
        "wifi_list.html", {"wifi_networks": Network().list_wifi()}, current_path, True
    )
    return HTMLResponse(content)


@rt.post("/wifi/connect", response_class=HTMLResponse)
async def wifi_connect(ssid: str = Form(), password: str = Form()):
    Network().connect_wifi(ssid, password)
    return HTMLResponse("OK")


@rt.post("/wifi/try_connect", response_class=HTMLResponse)
async def wifi_try_connect(
    ssid: str = Form(),
):
    Network().try_connect_wifi(ssid)
    return HTMLResponse("OK")


@rt.post("/wifi/disconnect", response_class=HTMLResponse)
async def wifi_disconnect():
    Network().disconnect_wifi()
    return HTMLResponse("OK")
