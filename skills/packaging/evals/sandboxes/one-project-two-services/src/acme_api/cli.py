import click
from pydantic import BaseModel

from acme_shared import total


class Order(BaseModel):
    amounts: list[str]


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    order = Order(amounts=list(amounts))
    click.echo(f"order total {total(order.amounts):.2f}")
