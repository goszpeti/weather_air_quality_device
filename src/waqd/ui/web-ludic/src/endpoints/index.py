from ludic.catalog.headers import H1

from ..components import Hello
from ..main import app
from ..pages import Page


@app.get("/")
async def homepage() -> Page:
    return Page(
        H1("WAQD2 Homepage"),
    )
