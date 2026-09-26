"""Create the development data: 2,000 customers, 200,000 orders (database beanie_shop)."""

import asyncio
import datetime as dt
import os
import random

from beanie import init_beanie
from pymongo import AsyncMongoClient

from models import Customer, Order


async def main() -> None:
    client = AsyncMongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))
    await client.drop_database("beanie_shop")
    await init_beanie(database=client["beanie_shop"], document_models=[Customer, Order])
    rng = random.Random(7)
    await Customer.insert_many([Customer(name=f"Customer {i}", country=rng.choice(["DE", "FR", "BE"])) for i in range(2000)])
    customers = await Customer.find_all().to_list()
    start = dt.datetime(2025, 1, 1, tzinfo=dt.UTC)
    batch = []
    for i in range(200_000):
        batch.append(Order(customer=rng.choice(customers), status=rng.choice(["paid", "shipped", "shipped", "cancelled"]),
                           total_cents=rng.randrange(100, 50_000), created_at=start + dt.timedelta(seconds=rng.randrange(40_000_000))))
        if len(batch) == 10_000:
            await Order.insert_many(batch)
            batch = []
    print(await Order.count(), "orders")


if __name__ == "__main__":
    asyncio.run(main())
