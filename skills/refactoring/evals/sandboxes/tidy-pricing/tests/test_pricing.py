from shop.pricing import basket_total, discount, fmt, price_with_vat


def test_price_with_vat():
    assert price_with_vat(10) == 12.0


def test_basket_total():
    assert basket_total([("a", 1.5), ("b", 2.0)]) == 3.5


def test_fmt():
    assert fmt(3) == "3.00 EUR"
    assert fmt(3, "USD") == "$3.00"


def test_discount_codes():
    assert discount(100, "SPRING10") == 90
    assert discount(100, "NOPE") == 100
