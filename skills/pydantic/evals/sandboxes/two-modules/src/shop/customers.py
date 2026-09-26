from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from shop.orders import Order


class Customer(BaseModel):
    name: str
    orders: list[Order] = []
