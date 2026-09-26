from decimal import Decimal

from shop.checkout import order_total


def test_small_basket_pays_shipping():
    assert order_total([{"price": "3.00", "qty": 2}], {}) == Decimal("10.90")


def test_bulk_discount_on_twelve_items():
    assert order_total([{"price": "5.00", "qty": 12}], {}) == Decimal("57.00")


def test_loyalty_credit():
    assert order_total([{"price": "60.00", "qty": 1}], {"loyal": True}) == Decimal("58.00")


def test_never_below_zero():
    assert order_total([{"price": "1.00", "qty": 1}], {"loyal": True}) == Decimal("4.90")
