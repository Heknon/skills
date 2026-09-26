from datetime import date

import pytest

from app.helpers import parse_date, slug


@pytest.mark.parametrize("raw", ["2026-03-01", "01/03/2026", " 01.03.2026 "])
def test_parse_date_formats(raw):
    assert parse_date(raw) == date(2026, 3, 1)


def test_parse_date_rejects_unknown():
    with pytest.raises(ValueError, match="unknown date format"):
        parse_date("March 1st")


def test_slug():
    assert slug("Ada  Lovelace") == "ada-lovelace"
