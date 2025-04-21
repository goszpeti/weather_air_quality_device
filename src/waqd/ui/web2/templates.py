from functools import partial
from pathlib import Path
from fastapi.responses import HTMLResponse
from htmlmin.main import minify

from jinja2 import Environment, FileSystemLoader

extra_minify = partial(minify, remove_comments=True, remove_empty_space=True)
current_path = Path(__file__).parent.resolve()
env = Environment(loader=FileSystemLoader(str(current_path)))

def simple_template(file_name: str, context: dict[str,str]) -> str:
    template = env.get_template(file_name)
    return minify(template.render(context), remove_comments=True, remove_empty_space=True)

def render_spa(request, content: str):
    tpl = simple_template("index.html", {"content": content})
    return HTMLResponse(content=extra_minify(tpl), status_code=200)
