from pathlib import Path

import click

from acme_reports.loaders import load_rows
from acme_reports.renderers.text import render


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def main(path: Path) -> None:
    click.echo(render(load_rows(path)))
