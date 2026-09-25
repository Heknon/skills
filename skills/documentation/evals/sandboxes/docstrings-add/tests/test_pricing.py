from decimal import Decimal

import pytest

from shop.pricing import add_vat, apply_discount, price_list, reprice, sku_label


def test_add_vat():
    assert add_vat(Decimal("10.00")) == Decimal("11.70")


def test_apply_discount():
    assert apply_discount(Decimal("10.00"), 25) == Decimal("7.50")
    with pytest.raises(ValueError):
        apply_discount(Decimal("10.00"), 120)


def test_price_list():
    assert price_list("toys") == {"a-1": Decimal("11.70"), "b-2": Decimal("2.93")}


def test_reprice_changes_items():
    items = [{"price": Decimal("10.00")}]
    reprice(items, 10)
    assert items[0]["price"] == Decimal("9.00")


def test_sku_label():
    assert sku_label("a-1") == "A-1"
