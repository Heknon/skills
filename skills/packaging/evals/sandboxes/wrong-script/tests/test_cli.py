from click.testing import CliRunner

from acme.cli import make_cli


def test_hello():
    result = CliRunner().invoke(make_cli(), ["hello"])
    assert result.output == "hello\n"


def test_greet():
    result = CliRunner().invoke(make_cli(), ["greet", "ops"])
    assert result.output == "hello, ops\n"
