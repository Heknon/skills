from click.testing import CliRunner

from acme.api import main


def test_total_line():
    result = CliRunner().invoke(main, ["1.10", "2.20"])
    assert result.output == "total 3.30\n"
