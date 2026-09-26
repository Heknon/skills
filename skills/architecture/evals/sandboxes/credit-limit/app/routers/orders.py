from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_order_service
from app.services.orders import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderIn(BaseModel):
    customer_id: int
    amount_cents: int = Field(gt=0)


class OrderOut(BaseModel):
    id: int
    customer_id: int
    amount_cents: int


@router.post("", status_code=201)
def place_order(body: OrderIn, service: Annotated[OrderService, Depends(get_order_service)]) -> OrderOut:
    order = service.place(body.customer_id, body.amount_cents)
    return OrderOut(id=order.id, customer_id=order.customer_id, amount_cents=order.amount_cents)
