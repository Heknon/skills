from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_repo
from app.repository import OrderRepository

router = APIRouter()


class Line(BaseModel):
    sku: str
    qty: int
    unit_cents: int


class OrderIn(BaseModel):
    customer_id: str
    lines: list[Line]


class OrderOut(BaseModel):
    id: int
    customer_id: str
    total_cents: int


@router.post("/orders", status_code=201)
def place_order(body: OrderIn, repo: Annotated[OrderRepository, Depends(get_repo)]) -> OrderOut:
    customer = repo.customer(body.customer_id)
    if customer is None:
        raise HTTPException(404, "unknown customer")
    total = sum(line.qty * line.unit_cents for line in body.lines)
    if customer["tier"] == "gold" and total >= 10_000:
        total = total * 90 // 100  # gold customers: 10% off orders of 100.00 or more
    owed = repo.open_total(body.customer_id) + total
    if owed > customer["credit_limit_cents"]:
        raise HTTPException(409, f"credit limit exceeded: {owed} > {customer['credit_limit_cents']}")
    order_id = repo.add(body.customer_id, total)
    return OrderOut(id=order_id, customer_id=body.customer_id, total_cents=total)
