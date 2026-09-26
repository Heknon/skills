import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.errors import AccountUnavailableError, InsufficientFundsError
from app.repository import AccountRepository
from app.service import TransferService


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///bank.db"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


def get_transfer_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TransferService:
    return TransferService(AccountRepository(session))


class TransferIn(BaseModel):
    source_id: int
    target_id: int
    amount_cents: int = Field(gt=0)


@app.post("/transfers", status_code=204)
async def transfer(body: TransferIn,
                   service: Annotated[TransferService, Depends(get_transfer_service)]) -> None:
    try:
        await service.transfer(body.source_id, body.target_id, body.amount_cents)
    except (AccountUnavailableError, InsufficientFundsError) as e:
        raise HTTPException(409, str(e)) from e
