import html
import json
from functools import partial
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, TypedDict
from typing_extensions import NotRequired
import os
import plotly.graph_objects as go
import waqd
from bottle import (Jinja2Template, default_app, redirect, jinja2_template,
                    request, response, route, static_file)
from htmlmin.main import minify
from pint import Quantity
from plotly.graph_objs import Scattergl
from plotly.io import to_html
import waqd.app as app
from waqd.base.component import Component
from waqd.ui.web.web_session import LoginPlugin
from waqd.ui.web.authentification import UserAuth, validate_password, validate_username
from waqd.base.db_logger import InfluxSensorLogger
from waqd.base.system import RuntimeSystem
from waqd.settings import LOCATION, LOCATION_LATITUDE, LOCATION_LONGITUDE, OW_API_KEY, OW_CITY_IDS, Settings
from waqd.components import OpenWeatherMap
from waqd.ui import format_unit_disp_value
from waqd import base_path

extra_minify = partial(minify, remove_comments=True, remove_empty_space=True)


if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry


class SensorApi_0_1(TypedDict):
    api_ver: str
    temp: NotRequired[str]  # deg C
    hum: NotRequired[str]  # %
    baro: NotRequired[str]  # hPa
    co2: NotRequired[str]  # ppm
    tvoc: NotRequired[str]  # ppb
    dust: NotRequired[str]  # ug per m3
    light: NotRequired[str]  # lux



class UvcornServer(Component):

    def __init__(self, components: "ComponentRegistry", settings: "Settings", enabled=True,
                 user_session_secret="SECRET", user_api_key="API_KEY", user_default_pw="TestPw"):
        super().__init__(components, settings, enabled)
        self._server = None
        self._settings: Settings
        if self._disabled:
            return
        self._comps: "ComponentRegistry"
        self._user_api_key = user_api_key
        self._run_thread = Thread(name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()
        self._html_path = base_path / "ui" / "web" / "html"

    # Load user by id here
    def _run_server(self):
        # use programatic routing to connect class instance methods to routes
       
        # Can't start server from bottle, because it does not support stopping it without a hack
        import uvicorn
        self._ready = True
        self._server = uvicorn.run(
            "waqd.ui.web-ludic.src.main:app",
            #ludic_app,
            host="0.0.0.0",
            port=8080,
            reload=True,
        )

    def stop(self):
        # must stop, because wlan captive portal would block port 80?
        if self._server:
            self._server.server_close()
        try:
            self._run_thread.join(0)
        except:
            pass
