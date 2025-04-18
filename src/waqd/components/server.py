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


# Endpoint constants
ROUTE_WAQD = "/waqd"
ROUTE_WAQD_TEMP_HISTORY = "/waqd/temp_history"
ROUTE_WAQD_HUM_HISTORY = "/waqd/humidity_history"
ROUTE_WAQD_PRES_HISTORY = "/waqd/pressure_history"
ROUTE_WAQD_CO2_HISTORY = "/waqd/co2_history"
ROUTE_PLOTLY_JS = "/script/plotly.js"
ROUTE_JQUERY_JS = "/script/jquery.min.js"

ROUTE_CSS = "/style.css"
ROUTE_ABOUT = "/about"
ROUTE_SETTINGS = "/settings"
ROUTE_LOGIN = "/login"
ROUTE_LOGOUT = "/logout"
ROUTE_LOGIN_FAILED = "/login_failed"

ROUTE_CHANGE_USER_NAME = "/change_name"
ROUTE_CHANGE_PW = "/change_pw"
ROUTE_SET_OW_API_KEY = "/set_ow_api_key"
ROUTE_SET_LOCATION = "/set_location"

# API endpoint constants
ROUTE_API_REMOTE_EXT_SENSOR = "/api/remoteExtSensor"
ROUTE_API_REMOTE_INT_SENSOR = "/api/remoteIntSensor"
ROUTE_API_EVENTS_REMOTE_INT_SENSOR = "/api/events/remoteIntSensor"
ROUTE_API_EVENTS_REMOTE_EXT_SENSOR = "/api/events/remoteExtSensor"

EVENT_UPDATE_FREQ_S = 15


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

    def __init__(self, components: "ComponentRegistry", settings: "Settings", enabled=True,
                 user_session_secret="SECRET", user_api_key="API_KEY", user_default_pw="TestPw"):
        super().__init__(components, settings, enabled)
        self._server = None
        self._settings: Settings
        if self._disabled:
            return
        self._comps: "ComponentRegistry"
        self._user_api_key = user_api_key
        self._app = default_app()
        self._app.config['SECRET_KEY'] = user_session_secret
        self._run_thread = Thread(name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()
        self._html_path = base_path / "ui" / "web" / "html"
        self._login: LoginPlugin = self._app.install(LoginPlugin())
        self.user_auth = UserAuth(user_default_pw)

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
        route(ROUTE_SET_LOCATION, "POST", self.index)
        route(ROUTE_SET_OW_API_KEY, "POST", self.index)
        route(ROUTE_CHANGE_USER_NAME, "POST", self.index)
        route(ROUTE_CHANGE_PW, "POST", self.index)
        route(ROUTE_LOGIN, "POST", self.login)
        route(ROUTE_LOGIN_FAILED, "GET", self.index)
        route(ROUTE_LOGOUT, "GET", self.logout)
        route(ROUTE_CSS, "GET", self.css)
        route(ROUTE_WAQD_TEMP_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_HUM_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_PRES_HISTORY, "GET", self.plot_graph)
        route(ROUTE_WAQD_CO2_HISTORY, "GET", self.plot_graph)
        route(ROUTE_PLOTLY_JS, "GET", self.get_plotlyjs)
        route(ROUTE_JQUERY_JS, "GET", self.get_jqueryjs)

        # api endpoints
        route(ROUTE_API_REMOTE_EXT_SENSOR + "<args:re:.*>", "POST", self.post_sensor_values)
        route(ROUTE_API_REMOTE_INT_SENSOR + "<args:re:.*>", "POST", self.post_sensor_values)
        route(ROUTE_API_REMOTE_EXT_SENSOR + "<args:re:.*>", "GET", self.get_remote_exterior_values)
        route(ROUTE_API_REMOTE_INT_SENSOR + "<args:re:.*>", "GET", self.get_remote_interior_values)
        route(ROUTE_API_EVENTS_REMOTE_INT_SENSOR, "GET", self.trigger_event_remote_value)
        route(ROUTE_API_EVENTS_REMOTE_EXT_SENSOR, "GET", self.trigger_event_remote_value)
        # Can't start server from bottle, because it does not support stopping it without a hack
        from paste import httpserver
        self._ready = True
        self._server = httpserver.serve(self._app, host='0.0.0.0', port='80',
                                        daemon_threads=True, start_loop=False, use_threadpool=True)
        self._server.serve_forever()

    def stop(self):
        # must stop, because wlan captive portal would block port 80?
        if self._server:
            self._server.server_close()
        try:
            self._run_thread.join(0)
        except:
            pass

# HTML display endpoints

    def css(self):
        # TODO do as static file
        # 1 week
        max_age = "604800"
        if waqd.DEBUG_LEVEL > 0:
            max_age = "0"
        response = static_file("style.css", root=self._html_path)
        response.set_header("Cache-Control", f"public, max-age={max_age}")
        return response

    def login(self):
        try:
            username = request.forms.get('username')  # type: ignore
            password = request.forms.get('password')  # type: ignore
        except Exception:
            return redirect(ROUTE_LOGIN_FAILED)
        if self.user_auth.check_login(username, password):
            self._login.login_user(username)
            return redirect('/waqd')
        else:
            return redirect(ROUTE_LOGIN_FAILED)

    def change_user_name(self):
        new_username = request.forms.get('username', "")  # type: ignore
        old_username = self._login.get_user()
        # not changed
        if new_username == old_username:
            return "<p>Username unchanged.</p>"
        # validate username schema
        if not validate_username(new_username):
            return """<p>Username does not fit the following criteria:</p>
            <ul>
                <li>5 to 25 charachters with letters (upper and lowercase) and numbers.</li>
                <li>Allowed special characters are: _ - and .</li>
            </ul>
            """
        self.user_auth.change_user_name(old_username, new_username)
        self._login.login_user(new_username)
        return "<p>Changed name to " + new_username + " successfully!</p>"

    def change_password(self):
        username = self._login.get_user()
        old_pw = request.forms.get('old_password', "")  # type: ignore
        new_pw = request.forms.get('password', "")  # type: ignore
        # TOOD use bottle html template helper
        # validate pw
        if not validate_password(new_pw):
            return """<p>Username does not fit the following criteria:</p>
            <ul>
                <li>5 to 25 charachters with letters (upper and lowercase) and numbers.</li>
                <li>Allowed special characters are: _ - and .</li>
            </ul>
            """

        if self.user_auth.check_login(username, old_pw):
            self.user_auth.set_password(username, new_pw)
        return "<p>Password changed successfully!</p>"

    def set_location(self):

        new_location_id: str = request.forms.get("location", "")  # type: ignore
        if not new_location_id:
            return "<p>Please enter a location!</p>"
        try:
            loc_name, longitude, latitude = self.parse_location(new_location_id)
            self._settings.set(LOCATION, loc_name) # TODO Ingolstadt, Bavaria
            self._settings.set(LOCATION_LONGITUDE, longitude)
            self._settings.set(LOCATION_LATITUDE, latitude)

            self._comps.stop_component_instance(self._comps.weather_info)  # reset setting
            if app.qt_backchannel:  # re_init gui to update all values
                app.qt_backchannel.re_init_gui.emit()

        except Exception as e:
            self._settings.set(LOCATION, "Unknown")
            return "<p>Location set, but does not seem to work!</p>"
        finally:
            self._settings.save()
        return "<p>Location set successfully!</p>"

    @staticmethod
    def parse_location(location_input: str):
        # comes in form of London - England, United Kingdom(51.51ÂºE -0.13ÂºN 25m asl)
        # parse location string - optimistic way, not counting on malicious intent
        # no error handling, caller has to catch errors
        loc_name = location_input.split(",")[0].strip(" ")
        latitude = location_input.split("(")[1].split(" ")[0].split("Â")[0]
        longitude = location_input.split("(")[1].split(" ")[1].split("Â")[0]
        return (loc_name, longitude, latitude)

    def set_owa_api_key(self):
        new_key = request.forms.get("ow_api", "")  # type: ignore
        self._settings.set(OW_API_KEY, str(new_key))
        try:
            owm = OpenWeatherMap("2643743", str(new_key))
            owm.get_current_weather()
            self._comps.stop_component_instance(self._comps.weather_info)  # reset setting
        except Exception as e:
            return "<p>OpenWeatherMap API key set, but does not seem to work!</p>"
        finally:
            self._settings.save()
        return "<p>OpenWeatherMap API key set successfully!</p>"

    def logout(self):
        self._login.logout_user()
        return self.index()

    def get_static_file(self, path: str):
        response = static_file(path, root=waqd.assets_path)
        if path.endswith(".woff"):
            response.content_type = 'font/woff; charset=utf-8'
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

        top_msg = ""
        page_content = ""
        bottom_msg = ""
        if current_user:
            bottom_msg = f'<p class="login_msg">Logged in as {current_user}</p>'
        if route == ROUTE_ABOUT:
            page_content = self._get_about_subpage()
        elif route == ROUTE_WAQD:
            page_content = self._get_waqd_subpage()
        elif route == ROUTE_LOGIN:
            page_content = (self._html_path / "login.html").read_text()
        elif route == ROUTE_LOGOUT:
            bottom_msg = '<p class="login_msg" style="margin-bottom: 100px">Logged out successfully.</p>'
        elif route == ROUTE_LOGIN_FAILED:
            bottom_msg = '<p class="login_msg" style="margin-bottom: 20px;">Login Failed.\nCheck your credentials!</p>'
        elif route == ROUTE_SETTINGS:
            page_content = self._get_settings_subpage()
        elif route == ROUTE_CHANGE_USER_NAME:
            msg = self.change_user_name()
            page_content = self._get_settings_subpage()
            top_msg = f'<div class="login_msg" style="margin-bottom: 20px;">{msg}</div>'
        elif route == ROUTE_CHANGE_PW:
            msg = self.change_password()
            page_content = self._get_settings_subpage()
            top_msg = f'<div class="login_msg" style="margin-bottom: 20px;">{msg}</div>'
        elif route == ROUTE_SET_LOCATION:
            msg = self.set_location()
            page_content = self._get_settings_subpage()
            top_msg = f'<div class="login_msg" style="margin-bottom: 20px;">{msg}</div>'
        elif route == ROUTE_SET_OW_API_KEY:
            msg = self.set_owa_api_key()
            page_content = self._get_settings_subpage()
            top_msg = f'<div class="login_msg" style="margin-bottom: 20px;">{msg}</div>'
        menu = self.generate_menu()
        tpl = jinja2_template(str(self._html_path / "index.html"), menu=menu,
                              content=page_content, top_msg=top_msg, bottom_msg=bottom_msg)
        return extra_minify(tpl)

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

        page_content = (self._html_path / "popup.html").read_text()
        tpl = Jinja2Template(page_content)
        return extra_minify(tpl.render(title=f"{display_name} History", content=my_plot_div))


###### Subpages ######


    def _get_about_subpage(self):
        page_content = (self._html_path / "about.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render(version=waqd.__version__, platform=RuntimeSystem().platform)

    def _get_waqd_subpage(self):
        page_content = (self._html_path / "waqd.html").read_text()
        interior_data = self._get_interior_sensor_values(units=True)
        exterior_data = self._get_exterior_sensor_values(units=True)
        current_weather = self._comps.weather_info.get_current_weather()
        icon_rel_path = "weather_icons/wi-na.svg"  # default N/A
        if current_weather:
            icon_rel_path = current_weather.get_icon().relative_to(waqd.assets_path)
        # second pass
        tpl = Jinja2Template(page_content)
        return tpl.render(weather_icon=str(icon_rel_path),
                          temp=interior_data["temp"],
                          humidity=interior_data["hum"],
                          pressure=interior_data["baro"],
                          co2=interior_data["co2"],
                          temp_ext=exterior_data["temp"],
                          hum_ext=exterior_data["hum"]
                          )

    def _get_login_subpage(self):
        # Implement login (you can check passwords here or etc)
        page_content = (self._html_path / "login.html").read_text()
        tpl = Jinja2Template(page_content)
        return tpl.render()

    def _get_settings_subpage(self):
        # Implement login (you can check passwords here or etc)
        page_content = (self._html_path / "settings.html").read_text()
        tpl = Jinja2Template(page_content)
        location = self._settings.get_string(LOCATION)
        if not location or location.lower() == "unknown":
            location = "Search for your location..."
        return tpl.render(username=self._login.get_user(),  # ow_api_key=self._settings.get_string(OW_API_KEY)
                          location=location)


###### API endpoints ######

# args are given in the format ?Key=Value


    def trigger_event_remote_value(self):
        response.content_type = 'text/event-stream; charset=utf-8'
        response.set_header("Cache-Control", "no-cache")

        if not self._login.get_user():
            response.status = 403
            return response

        yield 'retry: 1000\n\n'
        route = request.path

        while True:
            sleep(EVENT_UPDATE_FREQ_S)
            values = {}
            if route == ROUTE_API_EVENTS_REMOTE_INT_SENSOR:
                values = self._get_interior_sensor_values(units=True)
            elif route == ROUTE_API_EVENTS_REMOTE_EXT_SENSOR:
                values = self._get_exterior_sensor_values(units=True)
            yield "data: " + json.dumps(values) + "\n\n"

    def _check_api_key(self, api_key):
        if api_key == self._user_api_key:
            return True
        return False

    def get_remote_exterior_values(self, args=""):
        # retrieve data for remote WAQD feature
        if not self._check_api_key(request.query.get("APPID", "")):  # type: ignore
            response.status = 403
            return response

        return self._get_exterior_sensor_values()

    def get_remote_interior_values(self, args=""):
        # retrieve data for remote WAQD feature
        if not self._check_api_key(request.query.get("APPID", "")):  # type: ignore
            response.status = 403
            return response

        return self._get_interior_sensor_values()

    def post_sensor_values(self, args=""):
        # Receive values for standalone hardware
        if not self._check_api_key(request.query.get("APPID", "")):  # type: ignore
            response.status = 403
            return response
        from waqd.app import comp_ctrl
        if not comp_ctrl:
            return
        data: SensorApi_0_1 = request.json  # type: ignore
        temp = None
        hum = None
        baro = None
        try:
            api_ver = data["api_ver"]
            if api_ver == "0.1":
                temp = float(data.get("temp", ""))
                hum = float(data.get("hum", ""))
                baro = float(data.get("baro", ""))
        except Exception:
            self._logger.debug(f"Server: Invalid response for /remoteSensor: {str(data)}")

        if "remoteExtSensor" in request.fullpath:
            comp_ctrl.components.remote_exterior_sensor.read_callback(temp, hum, baro)
        elif "remoteIntSensor" in request.fullpath:
            comp_ctrl.components.remote_interior_sensor.read_callback(temp, hum, baro)

        return response

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

        if temp is None or hum is None:
            current_weather = self._comps.weather_info.get_current_weather()
            if current_weather:
                temp = app.unit_reg.Quantity(current_weather.temp, "degC")
                hum = current_weather.humidity
        if units:  # format non unit values
            temp = self._format_sensor_disp_value(temp, True)
            hum = self._format_sensor_disp_value(hum, "%", 0)
        else:
            temp = self._format_sensor_disp_value(temp)
            hum = self._format_sensor_disp_value(hum, "")
        data: SensorApi_0_1 = {"api_ver": "0.1",
                               "temp": temp, "hum": hum,
                               "baro": "N/A", "co2": "N/A"
                               }
        return data

    def _format_sensor_disp_value(self, quantity: Quantity, unit=None, precision=1):
        disp_value = format_unit_disp_value(quantity, unit, precision)
        return html.escape(disp_value)

###### Script endpoints for offline access of js libs ######

    def get_plotlyjs(self):
        import plotly
        path = os.path.join(plotly.__file__, "..", "package_data")
        response = static_file("plotly.min.js", root=path)
        # 1 week
        max_age = "604800"
        if waqd.DEBUG_LEVEL > 1:
            max_age = "0"
        response.set_header("Cache-Control", f"public, max-age={max_age}")
        return response

    def get_jqueryjs(self):
        import js.jquery
        res = js.jquery.jquery
        response = static_file(js.jquery.jquery.minified, root=os.path.dirname(res.fullpath()))
        # 1 week
        max_age = "604800"
        if waqd.DEBUG_LEVEL > 1:
            max_age = "0"
        response.set_header("Cache-Control", f"public, max-age={max_age}")
        return response
