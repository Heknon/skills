"""Request and response models: the contract, and nothing else.

Keeping them apart from domain and database models is the architecture
skill's ground; this recipe is flat on purpose.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_partial import PartialModelMixin


class OrderIn(PartialModelMixin, BaseModel):
    """POST /orders body: the fields a client may write."""

    model_config = ConfigDict(extra="forbid")  # a misspelt key is a 422, not ignored

    customer: str = Field(min_length=1, max_length=80)
    quantity: int = Field(ge=1, le=100)
    note: str | None = Field(default=None, max_length=200)


class Order(OrderIn):
    """What the API returns, and the full model a PATCH result must pass.

    The server owns id, status, cancel_reason, created_at and revision: they are not in
    OrderIn, so a POST or PATCH body that sends them is a 422.
    """

    id: int
    status: Literal["open", "cancelled"] = "open"
    cancel_reason: str | None = None
    created_at: datetime
    revision: int = 1


# PATCH body: every field of OrderIn optional, defaults kept (pydantic
# skill, partial/build.md). The merged result is validated with Order.
OrderPatch = OrderIn.model_as_partial()


class CancelRequest(BaseModel):
    """POST /orders/{id}/cancel body: an action with a reason, not a field edit."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=200)


class OrderPage(BaseModel):
    """One page of GET /orders. `next_cursor` is null on the last page."""

    items: list[Order]
    next_cursor: str | None
