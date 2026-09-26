from ledger.cli import to_base


def test_usd_to_base():
    assert to_base("USD", 100) == 93.0
