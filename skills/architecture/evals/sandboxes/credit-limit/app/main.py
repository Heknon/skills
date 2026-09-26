from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import NotFoundError
from app.repositories.orders import Customer, OrderRepository
from app.routers.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo = OrderRepository()
    repo.customers[1] = Customer(id=1, credit_limit_cents=10_000)
    app.state.orders = repo
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(orders_router)


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)
