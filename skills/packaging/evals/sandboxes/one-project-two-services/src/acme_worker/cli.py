import click
import httpx

from acme_shared import total


def post(client: httpx.Client, value: str) -> int:
    return client.post("/totals", json={"total": value}).status_code


@click.command()
@click.argument("amounts", nargs=-1)
def main(amounts: tuple[str, ...]) -> None:
    click.echo(f"batch total {total(list(amounts)):.2f}")
