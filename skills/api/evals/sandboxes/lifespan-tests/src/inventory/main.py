from contextlib import asynccontextmanager

from fastapi import FastAPI, Request


class Pool:
    """Stands in for a database connection pool."""

    def __init__(self) -> None:
        self.open = True
        self.stock = {"bolt": 120, "nut": 0}

    def close(self) -> None:
        self.open = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = Pool()
    yield
    app.state.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/stock/{sku}")
def stock(sku: str, request: Request) -> dict:
    return {"sku": sku, "count": request.app.state.pool.stock.get(sku, 0)}
