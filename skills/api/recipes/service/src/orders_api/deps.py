"""Dependencies. What is injected and how layers are wired is the
architecture skill's ground; this file shows the FastAPI mechanics."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request

from orders_api.store import Store


def get_store(request: Request) -> Store:
    """The store the lifespan opened. Tests get a fresh one per `with TestClient(app)`."""
    return request.app.state.store


def get_clock() -> datetime:
    """Now, in UTC. Overridden in tests to make rows with equal timestamps."""
    return datetime.now(UTC)


StoreDep = Annotated[Store, Depends(get_store)]
Now = Annotated[datetime, Depends(get_clock)]
