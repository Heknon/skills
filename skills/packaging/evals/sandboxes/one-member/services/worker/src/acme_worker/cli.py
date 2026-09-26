import click

from acme_worker import run


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    """Total AMOUNTS as one batch."""
    click.echo(run(list(amounts)))
