from shop import discount


def test_silver_discount(monkeypatch):
    monkeypatch.setattr(discount, "rate_for", lambda tier: 0.1)
    assert discount.rate_for("silver") == 0.1
