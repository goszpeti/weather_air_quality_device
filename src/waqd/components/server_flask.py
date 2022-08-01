import html
from markupsafe import escape

import imp
import json
from random import random
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, TypedDict
import os
import waqd
import waqd.app
from bottle import (Jinja2Template, default_app, request, response,
                    static_file)
from flask import render_template, request, Flask, current_app, Response

from pint import Quantity
from waqd.assets import get_asset_file
from waqd.base.component import Component

if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry
app: Flask = None

class SensorApi_0_1(TypedDict):
    api_ver: str
    temp: str  # deg C
    hum: str  # %
    baro: str  # hPa
    co2: str  # ppm


class Server(Component):
    menu = {
        "/waqd": "Weather Air Quality Device",
        "/about": "About"
    }

    def __init__(self, components: "ComponentRegistry", enabled=True):
        Component.__init__(self, components, enabled=enabled)
        self._server = None
        if self._disabled:
            return
        self._comps: "ComponentRegistry"
        self._app = Flask(__name__)
        app = self._app

        self._app.config.from_mapping(
                SECRET_KEY='dev',
                # DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
            )
        self._run_thread = Thread(name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()

        @app.route('/')
        def hello():
            return self.get_entrypoint()
 
    def _run_server(self):
        # self._app.add_url_rule("/", "main", EndpointAction(self.hello))
        # self.register(self._app, route_base='/')

        # Can't start server rom bottle, because it does not support stopping it without a hack
        from paste import httpserver
        self._server = httpserver.serve(self._app, host='0.0.0.0', port='80',
                                        daemon_threads=True, start_loop=False)
        self._server.serve_forever()
        

    def stop(self):
        # must stop, because wlan captive portal would block port 80?
        if self._server:
            self._server.server_close()
        

### HTML display endpoints

    def get_static_file(self, path: str):
        return static_file(path, root=waqd.assets_path)

    def get_entrypoint(self):
        """ Single page entrypoint """
        page = get_asset_file("html", "index.html").read_text()
        tpl = Jinja2Template(page)
        page_content = ""
        path = request.path
        path = "/waqd" if path == "/" else path
        if request.path == "/about":
            page_content = self._get_about_subpage()
        elif request.path in "/waqd":
            page_content = self._get_waqd_subpage()
            
        menu = self._generate_menu(active_page=path)
        return tpl.render(menu=menu, content=page_content)

    def _generate_menu(self, active_page: str):
        active_name = self.menu.get(active_page, "")
        inactive_anchors = ""
        active_anchor = f'<a class = "active" href = "{active_page}" >{active_name}</a>'

        for ref, name in self.menu.items():
            if ref == active_page:
                continue
            inactive_anchors += f'<a class="passive" href="{ref}">{name}</a>'
        menu = f"""
        {active_anchor}
        <div id="myLinks">
            {inactive_anchors}
        </div>
        """
        return menu

    def _get_about_subpage(self):
        page_content = get_asset_file("html", "about.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()

    def _get_waqd_subpage(self):
        page_content = get_asset_file("html", "waqd.html").read_text()
        temp = self._comps.temp_sensor.get_temperature()
        temp_disp = self._format_sensor_disp_value(temp)
        hum_disp = self._format_sensor_disp_value(self._comps.humidity_sensor.get_humidity(), "%")
        co2_disp = self._format_sensor_disp_value(self._comps.co2_sensor.get_co2(), "ppm")
        baro_disp = self._format_sensor_disp_value(self._comps.pressure_sensor.get_pressure(), "hPa")
        current_weather = self._comps.weather_info.get_current_weather()
        icon_rel_path = "weather_icons/wi-na.svg"  # default N/A
        if current_weather:
            icon_rel_path = current_weather.icon.relative_to(waqd.assets_path)
        # second pass
        tpl = Jinja2Template(page_content)
        return tpl.render(weather_icon=str(icon_rel_path),
                          temp=temp_disp,
                          humidity=hum_disp,
                          pressure=baro_disp,
                          co2=co2_disp)

    def _format_sensor_disp_value(self, quantity, unit=None):
        disp_value = "N/A"
        if quantity is not None:
            if unit:
                disp_value = f"{int(quantity)} {unit}"
            if isinstance(quantity, Quantity):
                disp_value = f"{float(quantity.m_as(waqd.app.unit_reg.degC)):.3} °C"
        return escape(disp_value)


#### API endpoints

    def trigger_event_remote_value(self):
        response.content_type = 'text/event-stream'
        response.cache_control = 'no-cache'
        
        yield 'retry: 1000\n\n'
        while True:
            sleep(10)
            # TODO don't push updates if we don't read anything?
            yield "data: " + json.dumps(self.get_remote_interior_values(disp=True)) + "\n\n"

    def get_remote_exterior_values(self):
        temp = self._comps.remote_exterior_sensor.get_temperature()
        if temp is not None:
            temp = temp.m_as(waqd.app.unit_reg.degC)
        hum = self._comps.remote_exterior_sensor.get_humidity()

        if temp is None:
            pass
        data: SensorApi_0_1 = {"api_ver": "0.1",
                            "temp": str(temp), "hum": str(hum),
                            "baro": str(None), "co2": str(None)}
        return data

    def get_remote_interior_values(self, disp=False):
        temp = self._comps.temp_sensor.get_temperature()
        if disp:
            temp = self._format_sensor_disp_value(temp)
        elif temp is not None:
            temp = temp.m_as(waqd.app.unit_reg.degC)
        hum = self._comps.humidity_sensor.get_humidity()
        pres = self._comps.pressure_sensor.get_pressure()
        co2 = self._comps.co2_sensor.get_co2()
        if disp: # format non unit values
            hum = self._format_sensor_disp_value(hum, "%")
            pres = self._format_sensor_disp_value(pres, "hPa")
            co2 = self._format_sensor_disp_value(co2, "ppm")

        data: SensorApi_0_1 = {"api_ver": "0.1",
                            "temp": str(temp), "hum": str(hum),
                            "baro": str(pres), "co2": str(co2)
                            }
        return data

    def post_sensor_values(self):
        from waqd.app import comp_ctrl
        if not comp_ctrl:
            return
        data: SensorApi_0_1 = request.json  # type: ignore
        temp = 0
        hum = 0
        try:
            api_ver = data["api_ver"]
            if api_ver == "0.1":
                temp = float(data.get("temp", None))
                hum = float(data.get("hum", None))
        except:
            self._logger.debug(f"Server: Invalid response for /remoteSensor: {str(data)}")

        if "remoteExtSensor" in request.fullpath:
            comp_ctrl.components.remote_exterior_sensor.read_callback(temp, hum)
        elif "remoteIntSensor" in request.fullpath:
            comp_ctrl.components.remote_interior_sensor.read_callback(temp, hum)
