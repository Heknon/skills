import click
import httpx

from common.settings import currency
from worker.money import fmt, to_cents


def post_total(client: httpx.Client, cents: int) -> int:
    return client.post("/totals", json={"cents": cents}).status_code


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    cents = sum(to_cents(a) for a in amounts)
    click.echo(f"batch total {fmt(cents, currency())}")
