"""Startup. Beanie 2 runs on PyMongo's AsyncMongoClient; Motor is not used."""

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models import MODELS


async def init_db(uri: str, db_name: str, *, build_indexes: bool = False) -> AsyncMongoClient:
    """Service start: skip_indexes=True, so no listIndexes or createIndexes
    is sent and no pod waits for an index build. build_indexes=True is for
    the one-off index job (build_indexes.py) and for tests."""
    client = AsyncMongoClient(uri)
    await init_beanie(database=client[db_name], document_models=MODELS,
                      skip_indexes=not build_indexes)
    return client
