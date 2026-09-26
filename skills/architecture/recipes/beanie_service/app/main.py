import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.accounts.router import router as accounts_router
from app.db import init_db
from app.errors import AppError, ConflictError, NotFoundError

# One handler per category. Starlette picks the nearest class in the
# exception's MRO, so every subclass is covered (lab, Starlette 1.7.0).
STATUS = {NotFoundError: 404, ConflictError: 409}


def _handler(status: int):
    async def handle(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"code": exc.code, "detail": str(exc)}, status_code=status)

    return handle


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = await init_db(
        os.environ["MONGODB_URI"],
        os.environ.get("MONGODB_DB", "accounts"),
        build_indexes=os.environ.get("BUILD_INDEXES") == "1",
    )
    yield
    await app.state.mongo.close()


def create_app(*, connect: bool = True) -> FastAPI:
    """connect=False: no lifespan, for route tests whose service is a fake."""
    app = FastAPI(lifespan=lifespan if connect else None)
    app.include_router(accounts_router)
    for category, status in STATUS.items():
        app.add_exception_handler(category, _handler(status))
    return app


app = create_app()
