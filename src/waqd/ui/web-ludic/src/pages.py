from typing import override

from ludic.attrs import GlobalAttrs
from ludic.catalog.layouts import Center, Stack
from ludic.catalog.pages import Body, Head, HtmlPage
from ludic.components import Component
from ludic.html import meta, link, hr, img
from ludic.types import AnyChildren
from ludic.catalog.buttons import (
    Button,
    ButtonDanger,
    ButtonInfo,
    ButtonPrimary,
    ButtonSuccess,
)
from ludic.catalog.headers import H2, H3, H4
from ludic.catalog.layouts import (
    Box,
    Center,
    Cluster,
    Grid,
    Sidebar,
    Stack,
    Switcher,
    WithSidebar,
)
from ludic.catalog.typography import Paragraph
from ludic.html import b

from .components import Hello
from ludic.styles import themes

from ludic.html import body, head, html, link, meta, script, style, title


class Page(Component[AnyChildren, GlobalAttrs]):
    styles = style.use(
        lambda theme: {
            "body": {
                "background": "linear-gradient(175deg, rgba(103, 154, 199, 1) 0%, rgba(232, 159, 166, 1) 100%);",
            }
        }
    )
    @override
    def render(self) -> HtmlPage:
        body = Body(
            Center(
                Stack(
                    Box(
                        Cluster(
                            b("WAQD"),
                            Cluster(
                                Button("Measurements"),
                                Button("Settings"),
                                Button("About"),
                                Button("Logout"),
                            ),
                            # classes=["justify-space-between"],
                        ),
                        classes=["invert"],
                    ),
                    Switcher(
                        Stack(
                            H2("Exterior", anchor=False),
                            hr(
                                style={
                                    "width": "50%",
                                    "height": "2px",
                                    "border-width": "0",
                                    "margin-bottom": "20px",
                                    "color": "white",
                                    "background-color": "white",
                                }
                            ),
                            img(
                                src="static/wi-day-cloudy_white.svg",
                                style={"width": "200px"},
                            ),
                            H2("Interior", anchor=False),
                            # Box("Switcher Item 1"),
                            # Box("Switcher Item 2"),
                            # Box("Switcher Item 3"),
                        ),
                    ),
                ),
                style={
                    "margin-block": "2rem",
                },
            ),
            # style={
            #     "background": "",
            # },
            htmx_version="latest",
        )
        
        return HtmlPage(
            Head(
                meta(charset="utf-8"),
                link(rel="icon", href="/static/favicon.png"),
                title="WAQD2",
            ),
            Body(Hello(name="World"), body, classes=["waqd2"])
        )