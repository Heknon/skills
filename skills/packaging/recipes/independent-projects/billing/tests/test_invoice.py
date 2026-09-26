from acme_billing import Invoice


def test_amount():
    assert Invoice(lines=["1.10", "2.20"]).amount() == "3.30"
