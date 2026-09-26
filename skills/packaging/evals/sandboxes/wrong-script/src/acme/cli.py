import click


def make_cli() -> click.Group:
    """Build the command group; tests call this to get a fresh group."""

    @click.group()
    def cli() -> None:
        """Acme operations tools."""

    @cli.command()
    def hello() -> None:
        """Say hello."""
        click.echo("hello")

    @cli.command()
    @click.argument("name")
    def greet(name: str) -> None:
        """Greet NAME."""
        click.echo(f"hello, {name}")

    return cli


def main() -> None:
    make_cli()()
