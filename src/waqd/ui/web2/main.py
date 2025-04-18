
from functools import partial
from pathlib import Path
import waqd.app as base_app
import waqd

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from fastapi.middleware.gzip import GZipMiddleware

from htmlmin.main import minify
from .templates import simple_template

extra_minify = partial(minify, remove_comments=True, remove_empty_space=True)
current_path = Path(__file__).parent.resolve()

web_app = FastAPI(
    title="Waqd Web UI",
    description="Web UI for Waqd",
    version=waqd.__version__,
    debug=waqd.DEBUG_LEVEL > 0,
    # openapi_url=None,
)
web_app.mount("/static", StaticFiles(directory=str(waqd.assets_path)), name="static")
web_app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

@web_app.get("/",response_class=HTMLResponse)
async def root(request: Request):
    # tpl = (request, simple_template("waqd.html", {}))
    content = simple_template("waqd.html", {})
    tpl = simple_template("index.html", {"content": content})
    return HTMLResponse(content=tpl, status_code=200)

def render_spa(request, content: str):
    tpl = simple_template("index.html", {"content": content})
    return HTMLResponse(content=extra_minify(tpl), status_code=200)


if base_app.comp_ctrl is None:
    base_app.basic_setup()

