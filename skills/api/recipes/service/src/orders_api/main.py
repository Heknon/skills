"""The app: lifespan, routers, error handlers.

Run it:  uv run uvicorn orders_api.main:app --app-dir src --port 8000
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from orders_api import problems
from orders_api.routes import router
from orders_api.store import Store


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.store = Store()      # open connections here, not at import time
    yield
    app.state.store.close()        # runs on shutdown, and when a `with TestClient` block ends


app = FastAPI(title="Orders API", version="1.0.0", lifespan=lifespan)
problems.install(app)
app.include_router(router)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}
