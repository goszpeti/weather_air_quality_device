from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ludic.html import style
from ludic.styles import themes, types
from ludic.web import LudicApp
from ludic.web.routing import Mount
from starlette.staticfiles import StaticFiles

from .themes import theme

themes.set_default_theme(theme)


@asynccontextmanager
async def lifespan(_: LudicApp) -> AsyncIterator[None]:
    style.load(cache=True)
    yield


app = LudicApp(
    debug=True,
    lifespan=lifespan,
    routes=[Mount("/static", StaticFiles(directory="src/waqd/ui/web2/static"), name="static")],
)

import waqd.ui.web2.src.endpoints.index  # noqa
import waqd.ui.web2.src.endpoints.errors  # noqa


