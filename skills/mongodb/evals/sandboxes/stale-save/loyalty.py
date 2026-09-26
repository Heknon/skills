"""Nightly job: recompute loyalty points for every customer.

The support desk changes emails and addresses through the API while
this job runs (it takes about two hours).
"""

import asyncio

from models import Customer


async def points_for(customer: Customer) -> int:
    await asyncio.sleep(0.5)  # stands in for the call to the billing service
    return 42


async def recompute(customer_id) -> None:
    customer = await Customer.get(customer_id)
    points = await points_for(customer)
    customer.loyalty_points = points
    await customer.save()


async def run_all() -> None:
    async for customer in Customer.find_all():
        await recompute(customer.id)
