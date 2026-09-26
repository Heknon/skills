from decimal import Decimal

from acme.core import total


def test_total():
    assert total(["1.10", "2.20"]) == Decimal("3.30")
