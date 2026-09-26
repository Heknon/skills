import click


@click.command()
@click.argument("path")
def main(path: str) -> None:
    """Sync the notes file at PATH (the HTTP client is not written yet)."""
    click.echo(f"would sync {path}")
