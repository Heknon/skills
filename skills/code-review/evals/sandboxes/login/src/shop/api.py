"""HTTP routes for API clients."""

import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.collection import Collection

from shop.clients import ClientDoc, find_client

app = FastAPI()
_mongo: MongoClient[ClientDoc] | None = None


def get_clients() -> Collection[ClientDoc]:
    global _mongo
    if _mongo is None:
        _mongo = MongoClient(os.environ.get("MONGODB_URL", "mongodb://localhost:27017"))
    return _mongo["shop"]["clients"]


class Credentials(BaseModel):
    client_id: str
    api_key: str


class ScopesOut(BaseModel):
    client_id: str
    scopes: list[str]


@app.post("/auth/scopes")
def client_scopes(
    body: Credentials,
    clients: Annotated[Collection[ClientDoc], Depends(get_clients)],
) -> ScopesOut:
    found = find_client(clients, body.client_id, body.api_key)
    if found is None:
        raise HTTPException(status_code=401, detail="unknown client or key")
    return ScopesOut(client_id=found["client_id"], scopes=found["scopes"])
