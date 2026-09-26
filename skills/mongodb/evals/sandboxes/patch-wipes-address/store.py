"""Customer storage. The PATCH endpoint validates the body with pydantic
(the pydantic skill's apply_patch) and passes `changes` here: a nested
dict holding only what the body set, such as {"address": {"city": "Lyon"}}.
"""

from typing import Any

from pydantic import BaseModel


class Address(BaseModel):
    street: str
    city: str
    zip: str


class Customer(BaseModel):
    name: str
    email: str | None = None
    address: Address
    tags: list[str] = []
    rev: int = 1


def save_patch(coll, customer_id: Any, changes: dict[str, Any]) -> None:
    coll.update_one({"_id": customer_id}, {"$set": changes})
