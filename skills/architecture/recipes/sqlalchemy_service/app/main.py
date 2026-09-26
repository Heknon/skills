import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.accounts.router import router as accounts_router
from app.db import Base, make_sessionmaker
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
    engine, app.state.sessionmaker = make_sessionmaker(
        os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///accounts.db")
    )
    # CREATE_TABLES=1 for local runs; a real service uses migrations
    if os.environ.get("CREATE_TABLES") == "1":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(accounts_router)
    for category, status in STATUS.items():
        app.add_exception_handler(category, _handler(status))
    return app


app = create_app()
