"""Reads and writes with the number of commands each one sends."""

from typing import Any

from beanie.exceptions import RevisionIdWasChanged
from beanie.operators import In

from app.models import Customer, CustomerCard, Order


class Conflict(Exception):
    """The document changed since it was read: the api skill maps it (409 or retry)."""


async def recent_orders(status: str, limit: int = 50) -> list[dict[str, Any]]:
    """Two commands whatever the limit: the orders (index status_1_created_at_-1),
    then one $in for their customers. Not fetch_links=True: Beanie puts its
    $lookup before $sort and $limit, so every matching order is looked up."""
    orders = await Order.find(Order.status == status).sort(-Order.created_at).limit(limit).to_list()
    ids = list({o.customer.ref.id for o in orders})
    names = {c.id: c.name for c in await Customer.find(In(Customer.id, ids)).to_list()}
    return [{"id": str(o.id), "total_cents": o.total_cents, "customer": names.get(o.customer.ref.id)}
            for o in orders]


async def customer_cards(city: str) -> list[CustomerCard]:
    """Projection: the server returns name and email only."""
    return await Customer.find(Customer.address.city == city).project(CustomerCard).to_list()


async def patch_customer(customer: Customer, set_doc: dict[str, Any]) -> Customer:
    """Write a dotted $set (from patch_to_set) filtered on the revision the
    customer was read with. One findAndModify."""
    if not set_doc:
        return customer
    try:
        return await customer.set(set_doc)
    except RevisionIdWasChanged as e:
        raise Conflict(str(customer.id)) from e


async def add_points(customer: Customer, points: int) -> Customer:
    """A change of one field: $inc of that field, never save() of a copy."""
    return await customer.inc({Customer.loyalty_points: points})
