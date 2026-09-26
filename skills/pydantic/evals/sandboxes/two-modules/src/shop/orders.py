from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from shop.customers import Customer


class Order(BaseModel):
    id: int
    customer: Customer | None = None
