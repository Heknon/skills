from datetime import datetime, timedelta
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()


class Order(BaseModel):
    id: int
    created_at: datetime
    total: float


# Orders arrive in batches: many share the same created_at to the second.
_START = datetime(2026, 9, 1, 12, 0, 0)
ORDERS: list[Order] = [
    Order(id=i, created_at=_START + timedelta(seconds=i // 4), total=10.0 + i)
    for i in range(1, 41)
]


class OrderPage(BaseModel):
    items: list[Order]
    offset: int
    limit: int


@app.get("/orders")
def list_orders(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> OrderPage:
    # Newest first. The store returns rows with equal keys in no fixed order.
    rows = sorted(ORDERS, key=lambda o: hash((o.id, offset)) % 97)
    rows = sorted(rows, key=lambda o: o.created_at, reverse=True)
    return OrderPage(items=rows[offset : offset + limit], offset=offset, limit=limit)
