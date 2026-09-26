# L3: a database model in a response or request body

**Rule.** No ORM row or Beanie `Document` is a path operation's request
body, return value or `response_model`. Requests parse into a schema;
responses are built from a schema; the repository returns domain models
(`core/boundary-models.md`).

**Why.** *lab* (FastAPI 0.141.1, Beanie 2.2.0): a returned `Document` with
no response model sent `password_hash`, `is_admin` and the id as `_id`,
and a missing document came back as `200 null`; a `Document` as the body
let a client set `is_admin` and even `_id`. With a response model the
output is filtered, but the row is still read after the session's work is
done: on SQLAlchemy async that raised `MissingGreenlet` inside a
`ResponseValidationError` (`sqlalchemy/loading.md`).

**Target.** The repository maps the row to a domain model while the
session is open; the route maps the domain model to the response schema.
The shapes below return a filtered row *before*, so the behaviour is the
same on both sides. A before that leaks is a bug: fix the leak first, then
reshape (refactoring decides; `core/boundary-models.md`).

## Before

```python file=before/app/main.py
import asyncio
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password_hash: Mapped[str]


engine = create_async_engine("sqlite+aiosqlite://")
Session = async_sessionmaker(engine, expire_on_commit=False)


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as s, s.begin():
        s.add(UserRow(id=1, email="ada@example.com", password_hash="h$1"))

asyncio.run(seed())
app = FastAPI()


async def get_session():
    async with Session() as s:
        yield s


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, s: Annotated[AsyncSession, Depends(get_session)]):
    return await s.scalar(select(UserRow).where(UserRow.id == user_id))   # the row itself
```

## After

```python file=after/app/main.py
import asyncio
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    password_hash: Mapped[str]


class User(BaseModel):                       # domain model
    id: int
    email: str
    password_hash: str


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        row = await self.session.scalar(select(UserRow).where(UserRow.id == user_id))
        if row is None:
            return None
        return User(id=row.id, email=row.email, password_hash=row.password_hash)


engine = create_async_engine("sqlite+aiosqlite://")
Session = async_sessionmaker(engine, expire_on_commit=False)


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as s, s.begin():
        s.add(UserRow(id=1, email="ada@example.com", password_hash="h$1"))

asyncio.run(seed())
app = FastAPI()


async def get_users():
    async with Session() as s:
        yield UserRepository(s)


class UserOut(BaseModel):                    # response schema
    id: int
    email: str


@app.get("/users/{user_id}")
async def get_user(user_id: int, users: Annotated[UserRepository, Depends(get_users)]) -> UserOut:
    user = await users.get(user_id)
    return UserOut(id=user.id, email=user.email)
```

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_response_has_only_public_fields():
    assert TestClient(app).get("/users/1").json() == {"id": 1, "email": "ada@example.com"}
```

The missing-user case (both sides answer 500 here) is left out on
purpose: it is a bug to fix separately, with a 404 (`core/errors.md`).
Checked with `uv run python check_shapes.py L3`. Steps: refactoring's
recipe `L3`.
