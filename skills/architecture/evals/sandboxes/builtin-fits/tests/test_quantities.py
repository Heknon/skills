import pytest

from app.cli import main
from app.quantities import parse_quantity


@pytest.mark.parametrize("text, expected", [("3", 3), (" 12 ", 12), ("1,000", 1000)])
def test_parse(text, expected):
    assert parse_quantity(text) == expected


def test_not_a_number():
    with pytest.raises(ValueError, match="not a whole number"):
        parse_quantity("three")


def test_cli_reports_bad_lines(capsys):
    assert main(["A1 2", "B2 x"]) == 1
    assert "line 2: not a whole number: 'x'" in capsys.readouterr().err
