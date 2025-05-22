from functools import lru_cache, partial
import functools
from pathlib import Path
from typing import Any
from fastapi.responses import HTMLResponse
from frozendict import frozendict
from htmlmin.main import minify

from jinja2 import Environment, FileSystemLoader

from waqd import DEBUG_LEVEL

from .authentication import PermissionChecker, UserInDB

extra_minify = partial(minify, remove_comments=True, remove_empty_space=True)
current_path = Path(__file__).parent.resolve()


def conditional_lru_cache(func):
    if DEBUG_LEVEL < 1:
        return lru_cache()(func)
    return func


def freezeargs(func):
    """Decorator to freeze mutable arguments (like dicts) to make them hashable for caching."""

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        args = (frozendict(arg) if isinstance(arg, dict) else arg for arg in args)
        kwargs = {k: frozendict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)

    return wrapped


@freezeargs
@conditional_lru_cache
def sub_template(
    file_name: str, context: dict[str, Any], root_path: Path, component=False
) -> str:
    if component:
        root_path = root_path / "components"
    else:
        root_path = root_path / "views"
    return base_template(file_name, context, root_path)


def base_template(file_name: str, context: dict[str, Any], root_path=current_path) -> str:
    # also include the parent, so we can use the components from the main template
    template_loader = FileSystemLoader(searchpath=[str(root_path), str(root_path.parent)])
    template_env = Environment(loader=template_loader)
    template = template_env.get_template(file_name)
    return minify(template.render(context), remove_comments=True, remove_empty_space=True)


def render_main(
    content: str, user: UserInDB | None, overflow=True, menu=True, toast=""
) -> HTMLResponse:
    """if overflow is false, on the RPI itself it will not scroll"""
    overflow_config = ""
    if not overflow:
        overflow_config = "overflow-scroll md:overflow-hidden lg:overflow-scroll"

    local = False
    if user:
        local = PermissionChecker(
            required_permissions=[
                "users:local",
            ]
        ).check_permissions(user)
    menu_content = ""
    if menu:
        menu_content = base_template(
            "views/menu.html",
            {
                "local": local,
                "logged_in": bool(user),
            },
            current_path,
        )
    tpl = base_template(
        "views/index.html",
        {
            "content": content,
            "overflow_config": overflow_config,
            "menu": menu_content,
            "toast": toast,
            "local": local,
        },
        current_path,
    )
    return HTMLResponse(content=extra_minify(tpl), status_code=200)
