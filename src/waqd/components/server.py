from datetime import datetime, timedelta
import os
from turtle import width
import plotly.graph_objects as go
from plotly.graph_objs import Scattergl
from plotly import offline
from plotly.io import to_html
import html
import json
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, List, Tuple, TypedDict
from waqd.components.sensor_logger import InfluxSensorLogger

import waqd
import waqd.app as app
from bottle import (Jinja2Template, default_app, request, response, route, redirect,
                    static_file)
from pint import Quantity
from waqd.assets import get_asset_file
from waqd.base.component import Component
from waqd.settings import USER_SESSION_SECRET
from .web_session import LoginPlugin, UserFileDB

if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry


class SensorApi_0_1(TypedDict):
    api_ver: str
    temp: str  # deg C
    hum: str  # %
    baro: str  # hPa
    co2: str  # ppm

# Endpoint constants
ROUTE_WAQD = "/waqd"
ROUTE_WAQD_TEMP_HISTORY = "/waqd/temp_history"
ROUTE_WAQD_HUM_HISTORY = "/waqd/humidity_history"
ROUTE_WAQD_PRES_HISTORY = "/waqd/pressure_history"
ROUTE_WAQD_CO2_HISTORY = "/waqd/co2_history"

ROUTE_CSS = "/style.css"
ROUTE_ABOUT = "/about"
ROUTE_SETTINGS = "/settings"
ROUTE_SIGNIN = "/login"
ROUTE_SIGNOUT = "/logout"
# ROUTE_PROFILE = "/profile"

# API endpoint constants
ROUTE_API_REMOTE_EXT_SENSOR = "/api/remoteExtSensor"
ROUTE_API_REMOTE_INT_SENSOR = "/api/remoteIntSensor"
ROUTE_API_EVENTS_REMOTE_INT_SENSOR = "/api/events/remoteIntSensor"

class BottleServer(Component):
    menu = {
        ROUTE_WAQD: "Measurements",
        ROUTE_ABOUT: "About",
        ROUTE_SETTINGS: "Settings",
        ROUTE_SIGNOUT: "Sign Out"
    }

    def __init__(self, components: "ComponentRegistry", enabled=True, user_session_secret="SECRET"):
        super().__init__(components, enabled=enabled)
        self._server = None
        if self._disabled:
            return
        self._comps: "ComponentRegistry"
        self._app = default_app()
        self._app.config['SECRET_KEY'] = user_session_secret
        self._run_thread = Thread(name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()
        self._user_settings = {}

        self._login = self._app.install(LoginPlugin())
        self._user_db = UserFileDB()
        # TODO Remove - add reg form 
        self._user_db.write_entry("goszpeti", "MyTestPw123$")


    # Load user by id here
    def _run_server(self):
        # use programatic routing to connect class instance methods to routes
        route('/static/<path:path>', 'GET', self.get_static_file)
        route('/', 'GET', self.index)
        route(ROUTE_ABOUT, 'GET', self.index)
        route(ROUTE_WAQD, 'GET', self.index)
        route(ROUTE_SIGNIN, 'GET', self.index)
        route(ROUTE_SIGNOUT, 'GET', self.index)
        route(ROUTE_SETTINGS, "GET", self.index)
        route(ROUTE_SIGNIN, 'POST', self.login)
        route(ROUTE_SIGNOUT, 'GET', self.logout)
        route(ROUTE_CSS, 'GET', self.css)
        route(ROUTE_WAQD_TEMP_HISTORY, 'GET', self.plot_graph)
        route(ROUTE_WAQD_HUM_HISTORY, 'GET', self.plot_graph)
        route(ROUTE_WAQD_PRES_HISTORY, 'GET', self.plot_graph)
        route(ROUTE_WAQD_CO2_HISTORY, 'GET', self.plot_graph)

        # api endpoints
        route(ROUTE_API_REMOTE_EXT_SENSOR, 'POST', self.post_sensor_values)
        route(ROUTE_API_REMOTE_INT_SENSOR, 'POST', self.post_sensor_values)
        route(ROUTE_API_REMOTE_EXT_SENSOR, 'GET', self.get_remote_exterior_values)
        route(ROUTE_API_REMOTE_INT_SENSOR, 'GET', self.get_remote_interior_values)
        route(ROUTE_API_EVENTS_REMOTE_INT_SENSOR, 'GET', self.trigger_event_remote_value)

        # Can't start server from bottle, because it does not support stopping it without a hack
        from paste import httpserver
        self._server = httpserver.serve(self._app, host='0.0.0.0', port='80',
                                        daemon_threads=True, start_loop=True)

    def stop(self):
        # must stop, because wlan captive portal would block port 80?
        if self._server:
            self._server.server_close()

### HTML display endpoints

    def css(self):
        response = static_file("style.css", root=waqd.assets_path / "html")
        response.set_header("Cache-Control", "public, max-age=0")
        return response

    def logout(self):
        # Implement logout
        self._login.logout_user()
        return redirect('/')

    def login(self):
        # TODO None checking
        username = request.forms.get('username')
        password = request.forms.get('password')
        if self._user_db.check_login(username, password):
            self._login.login_user(username)
            return redirect('/waqd')
        else:
            return "<p>Login failed.</p>" # TODO write to the same page

    def _get_login_subpage(self):
        # Implement login (you can check passwords here or etc)
        page_content = get_asset_file("html", "login.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()

    def get_static_file(self, path: str):
        response = static_file(path, root=waqd.assets_path)
        # 1 week
        response.set_header("Cache-Control", "public, max-age=0")  # 604800
        return response

    def index(self):
        """ Single page entrypoint """
        route = request.path
        # default entrypoint to waqd view
        if route == "/":
            redirect(ROUTE_WAQD)

        current_user = self._login.get_user()
        user_data = self._user_db.get_entry(current_user)
        if not current_user and route != ROUTE_SIGNIN:
            return redirect(ROUTE_SIGNIN)

        page = get_asset_file("html", "index.html").read_text()
        tpl = Jinja2Template(page)
        page_content = ""
        login_msg = ""
        if route == ROUTE_ABOUT:
            page_content = self._get_about_subpage()
        elif route == ROUTE_WAQD:
            page_content = self._get_waqd_subpage()
        elif route == ROUTE_SIGNIN:
            page_content = self._get_login_subpage()
        elif route == ROUTE_SIGNOUT:
            login_msg = "Logged out successfully."
        elif route == ROUTE_SETTINGS:
            page_content = ""

        menu = self._generate_menu()

        if current_user:
            login_msg = f'<p class="login_msg">Logged in as {current_user}</p>'
        return tpl.render(menu=menu, content=page_content, login_msg=login_msg)

    def plot_graph(self):
        time_m = 180
        my_plot_div = ""
        route = request.path
        sensor_type = ""
        display_name = ""
        if route == ROUTE_WAQD_TEMP_HISTORY:
            sensor_type = "temp_degC"
            display_name = "Temperature (°C)"
        elif route == ROUTE_WAQD_HUM_HISTORY:
            sensor_type = "humidity_%"
            display_name = "Humidity (%)"
        elif route == ROUTE_WAQD_PRES_HISTORY:
            sensor_type = "pressure_hPa"
            display_name = "Atmospheric pressure (hPa)"
        elif route == ROUTE_WAQD_CO2_HISTORY:
            sensor_type = "CO2_ppm"
            display_name = "CO2 (ppm)"
        if not sensor_type:
            return
        # TODO constants
        # pressure_hPa
        times_value_pairs = InfluxSensorLogger.get_sensor_values(
            "interior", sensor_type, time_m)
        if times_value_pairs:  # .isoformat(sep=" ")
            times = [times_value_pair[0].astimezone(waqd.LOCAL_TIMEZONE)
                    for times_value_pair in times_value_pairs]
            values = [times_value_pair[1] for times_value_pair in times_value_pairs]
            graph = Scattergl(x=times, y=values)
            fig = go.Figure(graph)
            my_plot_div = to_html(fig, default_width="auto", full_html=False)
            # my_plot_div = offline.plot(fig, include_plotlyjs=True, output_type='div')

        page_content = get_asset_file("html", "popup.html").read_text()
        tpl = Jinja2Template(page_content)
        # (waqd.base_path / "plotly.html").write_text(tpl.render(title="Temperature History", content=my_plot_div))
        return tpl.render(title=f"{display_name} History", content=my_plot_div)
        

    def _generate_menu(self):
        menu_items = ""
        for ref, name in self.menu.items():
            menu_items += f'<li><a href="{ref}">{name}</a></li>'
        menu = f"""
        <ul class="menu-items">
            {menu_items}
        </ul>
        """
        return menu
        # tpl = Jinja2Template(menu)
        # return tpl.render(user_name=user_name)

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
                disp_value = f"{float(quantity.m_as(app.unit_reg.degC)):.3} °C"
        return html.escape(disp_value)


#### API endpoints

    def trigger_event_remote_value(self):
        response.content_type = 'text/event-stream'
        response.set_header("Cache-Control", "no-cache")

        yield 'retry: 1000\n\n'
        while True:
            sleep(10)
            # TODO don't push updates if we don't read anything?
            yield "data: " + json.dumps(self.get_remote_interior_values(disp=True)) + "\n\n"

    def get_remote_exterior_values(self):
        temp = self._comps.remote_exterior_sensor.get_temperature()
        if temp is not None:
            temp = temp.m_as(app.unit_reg.degC)
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
            temp = temp.m_as(app.unit_reg.degC)
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