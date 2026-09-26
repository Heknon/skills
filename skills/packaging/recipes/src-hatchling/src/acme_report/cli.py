from importlib.resources import files

import click


def render(month: str, total: float) -> str:
    template = files("acme_report").joinpath("templates/report.txt").read_text()
    return template.format(month=month, total=f"{total:.2f}").rstrip("\n")


@click.command()
@click.argument("month")
@click.option("--total", type=float, default=0.0, help="Sales total for the month.")
def main(month: str, total: float) -> None:
    """Print the report line for MONTH."""
    click.echo(render(month, total))
