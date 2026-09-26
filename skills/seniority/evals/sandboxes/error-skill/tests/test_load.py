from decimal import Decimal
from pathlib import Path

from ledger.amounts import parse_amount
from ledger.load import load

DATA = Path(__file__).parent.parent / "data"


def test_parse_amount():
    assert parse_amount(" 12.50 ") == Decimal("12.50")


def test_unreadable_amounts_are_set_aside():
    assert load(DATA / "july.csv") == (Decimal("49.75"), [4])
