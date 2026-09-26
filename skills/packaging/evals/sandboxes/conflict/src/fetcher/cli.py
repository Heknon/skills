import click
import httpx


@click.command()
@click.argument("url")
def main(url: str) -> None:
    """Print the status of URL."""
    response = httpx.get(url, timeout=10)
    click.echo(response.status_code)
