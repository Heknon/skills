from click.testing import CliRunner

from notes.cli import main


def test_dry_message():
    result = CliRunner().invoke(main, ["a.md"])
    assert result.output == "would sync a.md\n"
