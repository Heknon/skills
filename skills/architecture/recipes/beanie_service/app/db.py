"""Startup and the client. Beanie 2 runs on PyMongo's AsyncMongoClient.
Index builds belong to a one-off job (the mongodb skill's recipes/beanie_app)."""

from beanie import init_beanie
from fastapi import Request
from pymongo import AsyncMongoClient

from app.accounts.models import AccountDocument

MODELS = [AccountDocument]


async def init_db(
    uri: str, db_name: str, *, build_indexes: bool = False
) -> AsyncMongoClient:
    client = AsyncMongoClient(uri)
    await init_beanie(
        database=client[db_name], document_models=MODELS, skip_indexes=not build_indexes
    )
    return client


def get_client(request: Request) -> AsyncMongoClient:
    return request.app.state.mongo
