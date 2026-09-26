from acme_tax.cli import gross


def test_germany():
    assert gross("DE", 100) == 119.0
