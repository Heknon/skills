import json
from datetime import datetime, timezone

from orders.api import order_response
from orders.schemas import OrderOut


def test_order_response_is_camel_case():
    order = OrderOut(order_id=7, total_cents=1250, placed_at=datetime(2026, 3, 1, tzinfo=timezone.utc))
    body = json.loads(order_response(order))
    assert body == {"orderId": 7, "totalCents": 1250, "placedAt": "2026-03-01T00:00:00Z"}


def test_order_accepts_camel_case_input():
    order = OrderOut.model_validate({"orderId": 7, "totalCents": 1, "placedAt": "2026-03-01T00:00:00Z"})
    assert order.order_id == 7
