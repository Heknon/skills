import pytest

from ledger.entries import balance


def test_balance():
    assert balance([("credit", 10), ("debit", 3)]) == 7


@pytest.mark.db
def test_balance_empty():
    assert balance([]) == 0
