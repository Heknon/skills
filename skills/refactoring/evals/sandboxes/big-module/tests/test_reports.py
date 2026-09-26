from datetime import datetime, timezone
from decimal import Decimal
from unittest import mock

from app import reports
from app.reports import Line, Order, format_money, order_total, render_text, write_csv

FIXED = datetime(2026, 3, 2, 9, 30, tzinfo=timezone.utc)


def orders():
    return [
        Order("A-1", "Ada", [Line("pen", 3, Decimal("1.25"))]),
        Order("A-2", "Linus", [Line("ink", 1, Decimal("7.10"))], currency="USD"),
    ]


def test_format_money():
    assert format_money(Decimal("1234.5")) == "€1,234.50"
    assert format_money(Decimal("-2.005"), "USD") == "-$2.01"
    assert format_money(Decimal("1"), "CHF") == "CHF 1.00"


def test_order_total_with_and_without_tax():
    order = orders()[0]
    assert order_total(order, with_tax=False) == Decimal("3.75")
    assert order_total(order) == Decimal("4.50")


def test_stamp_header_uses_clock():
    with mock.patch("app.reports.now", return_value=FIXED):
        assert reports.stamp_header("X") == "X - generated 2026-03-02 09:30 UTC"


def test_render_text():
    with mock.patch("app.reports.now", return_value=FIXED):
        text = render_text(orders(), title="Daily")
    assert text.splitlines()[0] == "Daily - generated 2026-03-02 09:30 UTC"
    assert "total USD" in text and "$8.52" in text


def test_write_csv(tmp_path):
    path = tmp_path / "out.csv"
    assert write_csv(path, orders()) == 2
    assert path.read_text(encoding="utf-8").splitlines()[1] == "A-1,Ada,EUR,3.75,0.75,4.50"
