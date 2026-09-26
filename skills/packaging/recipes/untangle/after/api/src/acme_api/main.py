import click

from acme_common.money import fmt
from acme_common.settings import currency
from acme_api.quotes import Quote


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
