"""Background jobs."""

import click

from acme_core import total


def run(batch: list[str]) -> str:
    return f"batch total {total(batch)}"


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    """Total AMOUNTS as one batch."""
    click.echo(run(list(amounts)))
