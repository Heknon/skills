from shop.orders import list_orders, revenue_cents
from shop.reports import report_line


def test_list_orders_of_a_customer() -> None:
    assert [order.id for order in list_orders("c-1")] == ["o-1", "o-2"]


def test_revenue_adds_the_orders() -> None:
    assert revenue_cents("c-1") == 5_500


def test_report_line() -> None:
    assert report_line("c-1") == "c-1: 2 orders, 5500 cents"
