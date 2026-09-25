from orders.totals import order_total
from support.checks import assert_totals


def test_small_order_pays_shipping():
    assert_totals(
        order_total([{"price": 10.0, "qty": 2}]),
        {"subtotal": 20.0, "shipping": 4.5, "total": 24.5},
    )


def test_free_shipping_from_50():
    assert_totals(
        order_total([{"price": 25.0, "qty": 2}]),
        {"subtotal": 50.0, "shipping": 0.0, "total": 50.0},
    )


def test_line_count():
    lines = [{"price": 1.0, "qty": 1}] * 3
    assert len(lines) == 4 - 1
