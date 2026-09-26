from rates import convert, rate


def test_usd_rate():
    assert rate("USD") == 1.08


def test_convert_gbp():
    assert convert(100, "GBP") == 85.0
