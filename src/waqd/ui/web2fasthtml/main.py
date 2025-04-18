
import waqd.app as base_app
import waqd
from waqd.ui.web2fasthtml.route_collector import add_routes
from fasthtml.common import Link, Style
from monsterui.all import *
# Choose a theme color (blue, green, red, etc)
hdrs = Theme.violet.local_headers()
custom_theme_css = Link(rel="stylesheet", href="/css/custom_theme.css", type="text/css")

web_app, rt = fast_app(
    static_path=str(waqd.assets_path),
    pico=False,
    surreal=False,
    hdrs=(
        hdrs,
        custom_theme_css,
        Link(
            rel="preload",
            href="font/Franzo-E4GA.woff",
            type="font/woff2",
            crossorigin="anonymous",
            _as="font",
        ),
        Style("""
@font-face {
font-family: MyFranzo;
src: url('font/Franzo-E4GA.woff');}"""),
    ),

    bodykw={"data-theme": "dark"},
)

# custom_theme_css,
web_app = add_routes(web_app)

if base_app.comp_ctrl is None:
    base_app.basic_setup()

