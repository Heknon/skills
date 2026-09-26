"""Database startup for the invoices service. TODO: connect and initialise Beanie."""

import os

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "invoices"


async def connect() -> None:
    raise NotImplementedError
