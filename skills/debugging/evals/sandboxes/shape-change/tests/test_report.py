from pathlib import Path

from stock.feed import load_items
from stock.report import stock_value

DATA = Path(__file__).parent.parent / "data"


def test_stock_value():
    items = [{"sku": "A1", "qty": 2, "price": 1.5}, {"sku": "B7", "qty": 1, "price": 3.0}]
    assert stock_value(items) == 6.0


def test_august_feed():
    assert stock_value(load_items(DATA / "feed-2026-08.json")) == 66.0
