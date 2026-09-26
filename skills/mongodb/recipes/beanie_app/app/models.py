"""Beanie 2.2.0 documents: what each setting sends to the server.

- use_revision: every update filters on revision_id and sets a new one;
  a stale write raises RevisionIdWasChanged (beanie/odm/documents.py).
- Settings.indexes and Indexed(...) are the record of the indexes the
  code needs. init_beanie creates them unless skip_indexes=True; on a
  large collection they are built by build_indexes.py, not at startup.
"""

import datetime as dt

from pydantic import BaseModel
from pymongo import ASCENDING, DESCENDING, IndexModel

from beanie import Document, Link


class Address(BaseModel):
    street: str
    city: str
    zip: str


class Customer(Document):
    name: str
    email: str
    address: Address
    tags: list[str] = []
    loyalty_points: int = 0

    class Settings:
        name = "customers"
        use_revision = True
        indexes = [IndexModel([("email", ASCENDING)], name="email_1", unique=True)]


class Order(Document):
    customer: Link[Customer]
    status: str
    total_cents: int
    created_at: dt.datetime

    class Settings:
        name = "orders"
        indexes = [
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)],
                       name="status_1_created_at_-1"),
        ]


class CustomerCard(BaseModel):
    """Projection model: find(...).project(CustomerCard) asks the server for
    these fields only (projection {"name": 1, "email": 1})."""

    name: str
    email: str


MODELS = [Customer, Order]
