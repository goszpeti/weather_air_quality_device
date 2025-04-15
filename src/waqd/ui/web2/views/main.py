from fasthtml.core import APIRouter
from fasthtml.common import *

import waqd
from waqd.ui.web2.views.components import LongUnderline
from .weather import SensorRetrieval

rt = APIRouter()

@rt("/weather_ext_refresh")
def weather_ext_refresh():
    return Div(exterior_widget(), id="weather_ext_repl")

@rt("/weather_int_refresh")
def weather_int_refresh():
    return Div(interior_widget(), id="weather_int_repl")

@rt.get
def dialog():
    hdr = Div(Button(aria_label="Close", rel="prev"), P('confirm'))
    ftr = Div(Button('Cancel', cls="secondary"), Button('Confirm'))
    return DialogX(
        "thank you!", header=hdr, footer=ftr, open=True, id="dlgtest"
    )  # 

@rt("/")
def get(request):
    return Body(
        Header(
            Div(
                A(H1(Strong("WAQD"))),
                Nav(
                    Ul(
                        Li(Button("Home", href="/", cls="secondary")),
                        Li(Button("Settings", href="/settings", cls="secondary")),
                        Li(Button("About", href="/about", cls="secondary")),
                        Li(
                            Details(
                                Summary("Account"),
                                Ul(
                                    Li(A("Profile"), href="#"),
                                    Li(A("Logout"), href="#"),
                                    dir="rtl",
                                ),
                                cls="dropdown",
                            ),
                        ),
                        # ,Button("≣", href="#", style="display:none;")
                    )
                ),
                cls="container",
            ),
            cls="is-fixed-above-lg is-fixed",
        ),
        Main(
            Grid(
                Card(
                    interior_widget(),
                    id="weather_int",
                    hx_trigger="every 10s",
                    hx_swap="innerHTML",
                    hx_get="/weather_int_refresh",
                    hx_target="this",
                ),
                Card(
                    exterior_widget(),
                    id="weather_ext",
                    hx_trigger="every 600s",
                    hx_swap="innerHTML",
                    hx_get="/weather_ext_refresh",
                    hx_target="this",
                ),
                Card(
                    H1("Forecast"),
                    id="weather_forecast",
                    # hx_trigger="every 5min",
                    # hx_swap="innerHTML",
                    # hx_get="/weather_ext_refresh",
                    # hx_target="#weather_ext_repl",
                ),
            ),
            cls="container",
        ),
        Footer(
            Div(
                H1("Footer"),
                P("This is the footer content."),
                cls="bg-gray-800 text-white p-4",
            ),
            cls="container",
        ),
    )

def exterior_widget():
    values = SensorRetrieval()._get_exterior_sensor_values(units=True)
    current_weather = SensorRetrieval()._comps.weather_info.get_current_weather()
    icon_rel_path = "weather_icons/wi-na.svg"  # default N/A
    if current_weather:
        icon_rel_path = current_weather.get_icon().relative_to(waqd.assets_path)
    return (
        H1("Exterior"),
        Div(
            Img(cls="svg-white", src=f"{icon_rel_path}", style="height: 200px"),
            id="weather_overall",
        ),
        LongUnderline(),
        Div(
            Img(
                cls="svg-white",
                src="weather_icons/wi-thermometer_full.svg",
                style="width: 100px",
            ),
            Span(values["temp"]),
            Button(
                "Details",
                hx_get=dialog,
                hx_target="body",
                hx_swap="beforeend",
            ),
            id="temp_ext_value",
            cls="row",
        ),
        Div(
            Img(cls="svg-white", src="weather_icons/wi-humidity.svg", style="width: 100px"),
            Span(values["hum"]),
            id="humidity_ext_value",
            cls="row",
        ),
    )

def interior_widget():
    values = SensorRetrieval()._get_interior_sensor_values(units=True)
    return (
        H1("Interior"),
        LongUnderline(),
        Div(
            Img(
                cls="svg-white",
                src="weather_icons/wi-thermometer_full.svg",
                style="width: 100px",
            ),
            Span(values["temp"]),
            id="temp_int_value",
            cls="row",
        ),
        Div(
            Img(cls="svg-white", src="weather_icons/wi-humidity.svg", style="width: 100px"),
            Span(values["hum"]),
            id="humidity_int_value",
            cls="row",
        ),
        Div(
            Img(src="general_icons/co2.svg", style="width: 100px"),
            Span(values["co2"]),
            id="humidity_int_value",
            cls="row",
        ),
    )