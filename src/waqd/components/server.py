import html
import json
from functools import partial
from re import I
from threading import Thread
from time import sleep
from typing import TYPE_CHECKING, List, TypedDict
from typing_extensions import NotRequired

import plotly.graph_objects as go
import waqd
import waqd.app as app
from bottle import (HTTPResponse, Jinja2Template, default_app, redirect,
                    request, response, route, static_file)
from htmlmin.main import minify
from pint import Quantity
from plotly.graph_objs import Scattergl
from plotly.io import to_html
from plotly.offline.offline import get_plotlyjs
from waqd.assets import get_asset_file
from waqd.base.component import Component
from waqd.components.sensor_logger import InfluxSensorLogger
from waqd.settings import USER_API_KEY

from .web_session import LoginPlugin, UserFileDB

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


# Endpoint constants
ROUTE_WAQD = "/waqd"
ROUTE_WAQD_TEMP_HISTORY = "/waqd/temp_history"
ROUTE_WAQD_HUM_HISTORY = "/waqd/humidity_history"
ROUTE_WAQD_PRES_HISTORY = "/waqd/pressure_history"
ROUTE_WAQD_CO2_HISTORY = "/waqd/co2_history"
ROUTE_PLOTLY_JS = "/script/plotly.js"

ROUTE_CSS = "/style.css"
ROUTE_ABOUT = "/about"
ROUTE_SETTINGS = "/settings"
ROUTE_LOGIN = "/login"
ROUTE_LOGOUT = "/logout"
ROUTE_LOGIN_FAILED = "/login_failed"

# API endpoint constants
ROUTE_API_REMOTE_EXT_SENSOR = "/api/remoteExtSensor"
ROUTE_API_REMOTE_INT_SENSOR = "/api/remoteIntSensor"
ROUTE_API_EVENTS_REMOTE_INT_SENSOR = "/api/events/remoteIntSensor"


class BottleServer(Component):
    menu_logged_in = {
        ROUTE_WAQD: "Measurements",
        ROUTE_SETTINGS: "Settings",
        ROUTE_ABOUT: "About",
        ROUTE_LOGOUT: "Logout",
    }
    menu_logged_out = {
        ROUTE_LOGIN: "Login",
        ROUTE_ABOUT: "About",
    }
    # pages which need the user to log in
    needs_login = [ROUTE_WAQD, ROUTE_SETTINGS]

    def __init__(self, components: "ComponentRegistry", enabled=True, user_session_secret="SECRET", user_api_key="API_KEY"):
        super().__init__(components, enabled=enabled)
        self._server = None
        if self._disabled:
            return
        self._comps: "ComponentRegistry"
        self._user_api_key = user_api_key
        self._app = default_app()
        self._app.config['SECRET_KEY'] = user_session_secret
        self._run_thread = Thread(name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()
        # currently user settings are the same as app settings
        # self._user_settings = {}
        # user_data = self._user_db.get_entry(current_user)

        self._login: LoginPlugin = self._app.install(LoginPlugin())
        self._user_db = UserFileDB()

    # Load user by id here
    def _run_server(self):
        # use programatic routing to connect class instance methods to routes
        route('/static/<path:path>', "GET", self.get_static_file)
        route('/static/script/<path:path>', "GET", self.get_static_file)
        route('/', "GET", self.index)
        route(ROUTE_ABOUT, "GET", self.index)
        route(ROUTE_WAQD, "GET", self.index)
        route(ROUTE_LOGIN, "GET", self.index)
        route(ROUTE_LOGOUT, "GET", self.index)
        route(ROUTE_SETTINGS, "GET", self.index)
        route(ROUTE_LOGIN, "POST", self.login)
        route(ROUTE_LOGIN_FAILED, "GET", self.index)
        route(ROUTE_LOGOUT, "GET", self.logout)
        route(ROUTE_CSS, "GET", self.css)
        route(ROUTE_WAQD_TEMP_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_HUM_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_PRES_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_CO2_HISTORY, "GET", self.plot_graph)
        route(ROUTE_PLOTLY_JS, "GET", self.get_plotlyjs)

        # api endpoints
        route(ROUTE_API_REMOTE_EXT_SENSOR + "<args:re:.*>", "POST", self.post_sensor_values)
        route(ROUTE_API_REMOTE_INT_SENSOR + "<args:re:.*>", "POST", self.post_sensor_values)
        route(ROUTE_API_REMOTE_EXT_SENSOR + "<args:re:.*>", "GET", self.get_remote_exterior_values)
        route(ROUTE_API_REMOTE_INT_SENSOR + "<args:re:.*>", "GET", self.get_remote_interior_values)
        route(ROUTE_API_EVENTS_REMOTE_INT_SENSOR, "GET", self.trigger_event_remote_value)

        # Can't start server from bottle, because it does not support stopping it without a hack
        from paste import httpserver
        self._server = httpserver.serve(self._app, host='0.0.0.0', port='80',
                                        daemon_threads=True, start_loop=True)

    def stop(self):
        # must stop, because wlan captive portal would block port 80?
        if self._server:
            self._server.server_close()

# HTML display endpoints

    def css(self):
        response = static_file("style.css", root=waqd.assets_path / "html")
        response.set_header("Cache-Control", "public, max-age=0")
        return response

    def login(self):
        try:
            username = request.forms.get('username')
            password = request.forms.get('password')
        except Exception:
            return redirect(ROUTE_LOGIN_FAILED)
        if self._user_db.check_login(username, password):
            self._login.login_user(username)
            return redirect('/waqd')
        else:
            return redirect(ROUTE_LOGIN_FAILED)

    def logout(self):
        self._login.logout_user()
        return self.index()

    def get_static_file(self, path: str):
        response = static_file(path, root=waqd.assets_path)
        # 1 week
        max_age = "604800"
        if waqd.DEBUG_LEVEL > 1:
            max_age = "0"
        response.set_header("Cache-Control", f"public, max-age={max_age}")
        return response

    def index(self):
        """ Single page entrypoint """
        route = request.path

        current_user = self._login.get_user()
        if not current_user and route in self.needs_login:
            return redirect(ROUTE_LOGIN)

        # default entrypoint to waqd view
        if route == "/":
            redirect(ROUTE_WAQD)

        page = get_asset_file("html", "index.html").read_text()
        tpl = Jinja2Template(page)
        page_content = ""
        login_msg = ""
        if current_user:
            login_msg = f'<p class="login_msg">Logged in as {current_user}</p>'
        if route == ROUTE_ABOUT:
            page_content = self._get_about_subpage()
        elif route == ROUTE_WAQD:
            page_content = self._get_waqd_subpage()
        elif route == ROUTE_LOGIN:
            page_content = get_asset_file("html", "login.html").read_text()
        elif route == ROUTE_LOGOUT:
            login_msg = '<p class="login_msg" style="margin-bottom: 100px">Logged out successfully.</p>'
        elif route == ROUTE_LOGIN_FAILED:
            login_msg = '<p class="login_msg" style="margin-bottom: 20px;">Login Failed.\nCheck your credentials!</p>'
        elif route == ROUTE_SETTINGS:
            page_content = self._get_settings_subpage()

        menu = self.generate_menu()

        return extra_minify(tpl.render(menu=menu, content=page_content, login_msg=login_msg))

    def generate_menu(self):
        menu_items = ""
        if not self._login.get_user():
            menu = self.menu_logged_out
        else:
            menu = self.menu_logged_in
        for ref, name in menu.items():
            menu_items += f'<li><a href="{ref}">{name}</a></li>'
        menu = f"""
        <ul class="menu-items">
            {menu_items}
        </ul>
        """
        return menu

    def get_plotlyjs(self):
        max_age = str(604800 * 12)  # 12 weeks
        response = HTTPResponse()
        response.set_header("Cache-Control", f"public, max-age={max_age}")
        response.set_header("Content-Type",  "application/javascript")
        response.content_type = "text/javascript"
        response.body = get_plotlyjs()
        return response

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
        times_value_pairs = InfluxSensorLogger.get_sensor_values("interior", sensor_type, time_m)
        if times_value_pairs:
            times = [times_value_pair[0].astimezone(waqd.LOCAL_TIMEZONE)
                     for times_value_pair in times_value_pairs]
            values = [times_value_pair[1] for times_value_pair in times_value_pairs]
            graph = Scattergl(x=times, y=values)
            fig = go.Figure(graph)
            fig.update_layout(
                yaxis=dict(range=[0, max(values) * 1.1]),
                margin=dict(l=20, r=20),
                paper_bgcolor="LightSteelBlue",)
            my_plot_div = to_html(fig, default_width="auto", include_plotlyjs=False, full_html=False)

        page_content = get_asset_file("html", "popup.html").read_text()
        tpl = Jinja2Template(page_content)
        return extra_minify(tpl.render(title=f"{display_name} History", content=my_plot_div))


###### Subpages ######


    def _get_about_subpage(self):
        page_content = get_asset_file("html", "about.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()

    def _get_waqd_subpage(self):
        page_content = get_asset_file("html", "waqd.html").read_text()
        interior_data = self._get_interior_sensor_values(units=True)
        current_weather = self._comps.weather_info.get_current_weather()
        icon_rel_path = "weather_icons/wi-na.svg"  # default N/A
        if current_weather:
            icon_rel_path = current_weather.icon.relative_to(waqd.assets_path)
        # second pass
        tpl = Jinja2Template(page_content)
        return tpl.render(weather_icon=str(icon_rel_path),
                          temp=interior_data["temp"],
                          humidity=interior_data["hum"],
                          pressure=interior_data["baro"],
                          co2=interior_data["co2"])

    def _get_login_subpage(self):
        # Implement login (you can check passwords here or etc)
        page_content = get_asset_file("html", "login.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()

    def _get_settings_subpage(self):
        # Implement login (you can check passwords here or etc)
        page_content = get_asset_file("html", "settings.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()


###### API endpoints ######

### args are given in the format ?Key=Value

    def trigger_event_remote_value(self):
        response.content_type = 'text/event-stream'
        response.set_header("Cache-Control", "no-cache")

        if not self._login.get_user():
            response.status = 403
            return response

        yield 'retry: 1000\n\n'
        while True:
            sleep(10)
            # TODO don't push updates if we don't read anything?
            yield "data: " + json.dumps(self._get_interior_sensor_values(units=True)) + "\n\n"

    def _check_api_key(self, api_key):
        if api_key == self._user_api_key:
            return True
        return False

    def _parse_api_args(self, args: str):
        args_dict = {}
        args_list = args.split("&")
        for arg in args_list:
            if "APPID" in arg.split("=")[0]:
                api_key = arg.split("=")[1]
                args_dict["api_key"] = api_key
        return args_dict

    def get_remote_exterior_values(self, args=""):
        # retrieve data for remote WAQD feature
        args_dict = self._parse_api_args(args)
        if not self._check_api_key(args_dict["api_key"]):
            response.status = 403
            return response

        return self._get_exterior_sensor_values()

    def get_remote_interior_values(self, args=""):
        # retrieve data for remote WAQD feature
        args_dict = self._parse_api_args(args)
        if not self._check_api_key(args_dict["api_key"]):
            response.status = 403
            return response

        return self._get_interior_sensor_values()

    def post_sensor_values(self, args=""):
        # Receive values for standalone hardware
        args_dict = self._parse_api_args(args)
        if not self._check_api_key(args_dict["api_key"]):
            response.status = 403
            return response
        from waqd.app import comp_ctrl
        if not comp_ctrl:
            return
        data: SensorApi_0_1 = request.json  # type: ignore
        temp = 0
        hum = 0
        try:
            api_ver = data["api_ver"]
            if api_ver == "0.1":
                temp = float(data.get("temp", ""))
                hum = float(data.get("hum", ""))
        except Exception:
            self._logger.debug(f"Server: Invalid response for /remoteSensor: {str(data)}")

        if "remoteExtSensor" in request.fullpath:
            comp_ctrl.components.remote_exterior_sensor.read_callback(temp, hum)
        elif "remoteIntSensor" in request.fullpath:
            comp_ctrl.components.remote_interior_sensor.read_callback(temp, hum)

    def _get_interior_sensor_values(self, units=False):
        temp = self._comps.temp_sensor.get_temperature()
        hum = self._comps.humidity_sensor.get_humidity()
        pres = self._comps.pressure_sensor.get_pressure()
        co2 = self._comps.co2_sensor.get_co2()
        temp_disp = self._format_sensor_disp_value(temp, units)

        if units: 
            hum = self._format_sensor_disp_value(hum, "%", 0)
            pres = self._format_sensor_disp_value(pres, "hPa", 0)
            co2 = self._format_sensor_disp_value(co2, "ppm", 0)
        else:
            hum = self._format_sensor_disp_value(hum, "", 0)
            pres = self._format_sensor_disp_value(pres, "", 0)
            co2 = self._format_sensor_disp_value(co2, "", 0)
        data: SensorApi_0_1 = {"api_ver": "0.1",
                               "temp": temp_disp, "hum": hum,
                               "baro": pres, "co2": co2
                               }
        return data

    def _get_exterior_sensor_values(self, units=False):
        temp = self._comps.remote_exterior_sensor.get_temperature()
        hum = self._comps.remote_exterior_sensor.get_humidity()
        if units:  # format non unit values
            temp = self._format_sensor_disp_value(temp, True)
            hum = self._format_sensor_disp_value(hum, "%")
        else:
            temp = self._format_sensor_disp_value(temp)
            hum = self._format_sensor_disp_value(hum, "")
        data: SensorApi_0_1 = {"api_ver": "0.1",
                               "temp": temp, "hum": hum,
                               "baro": "N/A", "co2": "N/A"
                               }
        return data

    def _format_sensor_disp_value(self, quantity, unit=None, precision=1):
        disp_value = "N/A"
        if quantity is not None:
            if isinstance(quantity, Quantity):
                # .m_as(app.unit_reg.degC)
                disp_value = f"{float(quantity.m):.{precision}f}"
                if unit:
                    disp_value += " " +app.unit_reg.get_symbol(str(quantity.u))
            else:
                disp_value = f"{float(quantity):.{precision}f}"
                if unit:
                    disp_value += " " + unit

        return html.escape(disp_value)
