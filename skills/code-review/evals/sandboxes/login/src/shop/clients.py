"""API clients and their keys."""

from typing import Any

from pymongo.collection import Collection

ClientDoc = dict[str, Any]


def find_client(
    clients: Collection[ClientDoc], client_id: str, api_key: str
) -> ClientDoc | None:
    """The client with this id and key, without the key; None if no match."""
    return clients.find_one(
        {"client_id": client_id, "api_key": api_key},
        {"_id": 0, "client_id": 1, "scopes": 1},
    )
