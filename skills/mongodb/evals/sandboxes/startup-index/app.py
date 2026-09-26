"""Service startup: every pod runs this before it takes traffic (4 replicas)."""

import os

from beanie import init_beanie
from pymongo import AsyncMongoClient

from models import Order


async def startup() -> None:
    client = AsyncMongoClient(os.environ["MONGODB_URI"])
    await init_beanie(database=client["shop"], document_models=[Order])


async def orders_for_email(email: str) -> list[Order]:
    return await Order.find(Order.customer_email == email).to_list()
