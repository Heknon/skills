import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.repository import OrderRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///orders.db"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.sessionmaker = async_sessionmaker(engine)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


def get_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> OrderRepository:
    return OrderRepository(session)


class LineIn(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


class OrderIn(BaseModel):
    customer: str
    lines: list[LineIn] = Field(min_length=1)


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sku: str
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer: str
    lines: list[LineOut]


@app.post("/orders", status_code=201)
async def create_order(body: OrderIn, repo: Annotated[OrderRepository, Depends(get_repo)]) -> OrderOut:
    order = await repo.add(body.customer, [(line.sku, line.quantity) for line in body.lines])
    return OrderOut.model_validate(order)
