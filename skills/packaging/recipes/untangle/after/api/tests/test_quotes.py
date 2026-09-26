from acme_api.quotes import Quote


def test_total():
    assert Quote(price="12.50", quantity=3).total_cents() == 3750
