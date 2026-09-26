"""HTTP routes for orders."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shop.orders import get_order

app = FastAPI()


class LineOut(BaseModel):
    sku: str
    qty: int
    unit_cents: int


class OrderOut(BaseModel):
    id: str
    lines: list[LineOut]


@app.get("/orders/{order_id}")
def read_order(order_id: str) -> OrderOut:
    order = get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderOut(
        id=order.id,
        lines=[
            LineOut(sku=line.sku, qty=line.qty, unit_cents=line.unit_cents)
            for line in order.lines
        ],
    )
