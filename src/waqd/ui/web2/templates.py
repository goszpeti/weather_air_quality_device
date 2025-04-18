from pathlib import Path
from htmlmin.main import minify

from jinja2 import Environment, FileSystemLoader

current_path = Path(__file__).parent.resolve()
env = Environment(loader=FileSystemLoader(str(current_path  / "views/html")))

def simple_template(file_name: str, context: dict[str,str]) -> str:
    template = env.get_template(file_name)
    return minify(template.render(context), remove_comments=True, remove_empty_space=True)