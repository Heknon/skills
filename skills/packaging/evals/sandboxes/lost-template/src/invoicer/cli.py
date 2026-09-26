import sys
from importlib.resources import files


def render(total: str) -> str:
    template = files("invoicer").joinpath("templates/report.html").read_text()
    return template.replace("{total}", total)


def main() -> None:
    total = sys.argv[1] if len(sys.argv) > 1 else "0.00"
    print(render(total))
