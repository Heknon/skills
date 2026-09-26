import click


def render(month: str, total: float) -> str:
    """Return one report line, such as 'Report 2026-08: 1200.50'."""
    return f"Report {month}: {total:.2f}"


@click.command()
@click.argument("month")
@click.option("--total", type=float, default=0.0, help="Sales total for the month.")
def main(month: str, total: float) -> None:
    """Print the report line for MONTH."""
    click.echo(render(month, total))
