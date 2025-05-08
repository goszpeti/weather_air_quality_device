from functools import partial
from pathlib import Path
from typing import Any
from fastapi.responses import HTMLResponse
from htmlmin.main import minify

from jinja2 import Environment, FileSystemLoader

extra_minify = partial(minify, remove_comments=True, remove_empty_space=True)
current_path = Path(__file__).parent.resolve()


def sub_template(
    file_name: str, context: dict[str, Any], root_path: Path, component=False
) -> str:
    if component:
        root_path = root_path / "components"
    return base_template(file_name, context, root_path)


def base_template(file_name: str, context: dict[str, Any], root_path=current_path) -> str:
    template_loader = FileSystemLoader(searchpath=str(root_path))
    template_env = Environment(loader=template_loader)
    template = template_env.get_template(file_name)
    return minify(template.render(context), remove_comments=True, remove_empty_space=True)


def render_spa(
    content: str, user_name: str | None, overflow=True, local=False, menu=True, toast=""
) -> HTMLResponse:
    """if overflow is false, on the RPI itself it will not scroll"""
    overflow_config = ""
    if not overflow:
        overflow_config = "overflow-scroll md:overflow-hidden lg:overflow-scroll"
    menu_content = ""
    if menu:
        menu_content = base_template(
            "menu.html",
            {
                "local": local,
                "logged_in": bool(user_name),
            },
            current_path,
        )
    tpl = base_template(
        "index.html",
        {
            "content": content,
            "overflow_config": overflow_config,
            "menu": menu_content,
            "toast": toast,
        },
        current_path,
    )
    return HTMLResponse(content=extra_minify(tpl), status_code=200)
