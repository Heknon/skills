from ledger.invoice import total


def test_total_adds_tax_once() -> None:
    assert total([(2, 10.0), (1, 5.0)]) == 30.0
