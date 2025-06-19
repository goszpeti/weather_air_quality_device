from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Body, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
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
    wifi_enabled = network.wifi_enabled()
    content = sub_template(
        "network_mgr.html",
        {"wifi_enabled": wifi_enabled},
        current_path,
    )
    return render_main(content, current_user)


@rt.post("/wifi/toggle")
async def toggle_wifi():
    network = Network()
    if network.wifi_enabled():
        network.disable_wifi()
    else:
        network.enable_wifi()
    return Response(status_code=204)


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


class WifiConnectRequest(BaseModel):
    ssid: str
    password: str

@rt.post("/wifi/connect")
async def wifi_connect(data: WifiConnectRequest = Body(...)):
    try:
        Network().connect_wifi(data.ssid, data.password)
        return Response(status_code=204)
    except Exception:
        return Response(status_code=400)

@rt.post("/wifi/try_connect")
async def wifi_try_connect(ssid: str = Form()):
    try:
        Network().try_connect_wifi(ssid)
        return Response(status_code=204)
    except Exception:
        return Response(status_code=401)

@rt.post("/wifi/disconnect")
async def wifi_disconnect():
    try:
        Network().disconnect_wifi()
        return Response(status_code=204)
    except Exception:
        return Response(status_code=400)
