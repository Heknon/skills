"""Create the development data: 1,000 customers (database loyalty)."""

import asyncio
import os

from beanie import init_beanie
from pymongo import AsyncMongoClient

from models import Address, Customer


async def main() -> None:
    client = AsyncMongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))
    await client.drop_database("loyalty")
    await init_beanie(database=client["loyalty"], document_models=[Customer])
    await Customer.insert_many([
        Customer(name=f"Customer {i}", email=f"c{i}@example.com",
                 address=Address(street=f"{i} Main St", city="Paris", zip="75001"))
        for i in range(1000)
    ])
    print(await Customer.count(), "customers")


if __name__ == "__main__":
    asyncio.run(main())
