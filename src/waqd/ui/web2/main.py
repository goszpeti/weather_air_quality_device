
import waqd.app as base_app
import waqd
from waqd.ui.web2.route_collector import add_routes
from fasthtml.common import Link, Style, fast_app

custom_theme_css = Link(rel="stylesheet", href="/css/custom_theme.css", type="text/css")


web_app, rt = fast_app(
    static_path=str(waqd.assets_path),
    pico=True,
    hdrs=(custom_theme_css,),
    bodykw={"data-theme":"dark"},
)
# Link(rel="preload", href="font/Franzo-E4GA.woff", type="font/woff2"),
# Style(""" @font-face {
# font-family: MyFranzo;
# src: url('font/Franzo-E4GA.woff');}"""),
# custom_theme_css,
web_app = add_routes(web_app)

if base_app.comp_ctrl is None:
    base_app.basic_setup()

