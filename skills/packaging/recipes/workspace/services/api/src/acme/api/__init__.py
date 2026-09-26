"""Order totals over the command line."""

import click

from acme.core import total


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    """Print the total of AMOUNTS."""
    click.echo(f"total {total(list(amounts))}")
