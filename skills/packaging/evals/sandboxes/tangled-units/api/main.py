import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import click

from common.money import fmt
from common.settings import currency
from quotes import Quote


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("price")
@click.argument("quantity", type=int)
def quote(price: str, quantity: int) -> None:
    q = Quote(price=price, quantity=quantity)
    click.echo(f"quote {fmt(q.total_cents(), currency())}")


if __name__ == "__main__":
    cli()
