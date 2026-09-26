import click

from report.render import render


@click.command()
@click.argument("month")
@click.option("--total", type=float, default=0.0, help="Sales total for the month.")
def main(month: str, total: float) -> None:
    """Print the report line for MONTH."""
    click.echo(render(month, total))
