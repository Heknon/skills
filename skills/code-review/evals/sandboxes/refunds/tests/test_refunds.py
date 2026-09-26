from datetime import date

from shop.refunds import Order, refundable

DELIVERED = Order(id="o-1", total_cents=4_000, delivered_on=date(2026, 3, 1))


def test_refundable_on_the_last_day() -> None:
    assert refundable(DELIVERED, date(2026, 3, 31))


def test_not_refundable_after_the_window() -> None:
    assert not refundable(DELIVERED, date(2026, 4, 1))
