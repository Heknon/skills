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
reshape (refactoring decides; `core/boundary-models.md`). The new
provider takes `get_session` through `Depends` instead of replacing it,
so a test's override of `get_session` still reaches the route
(`core/wiring.md`).

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


async def get_session():
    async with Session() as s:
        yield s


async def get_users(s: Annotated[AsyncSession, Depends(get_session)]) -> UserRepository:
    return UserRepository(s)


class UserOut(BaseModel):                    # response schema
    id: int
    email: str


@app.get("/users/{user_id}")
async def get_user(user_id: int, users: Annotated[UserRepository, Depends(get_users)]) -> UserOut:
    user = await users.get(user_id)
    if user is None:   # a 500 before the reshape too: a bug kept, fixed apart
        raise LookupError(f"user {user_id} not found")
    return UserOut(id=user.id, email=user.email)
```

## The test both pass

```python file=test_shape.py
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import Base, UserRow, app, get_session


def test_response_has_only_public_fields():
    assert TestClient(app).get("/users/1").json() == {"id": 1, "email": "ada@example.com"}


def test_an_override_of_get_session_reaches_the_route():
    engine = create_async_engine("sqlite+aiosqlite://")
    own = async_sessionmaker(engine, expire_on_commit=False)

    async def seed() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with own() as s, s.begin():
            s.add(UserRow(id=1, email="test@example.com", password_hash="t"))

    async def own_session():
        async with own() as s:
            yield s

    asyncio.run(seed())
    app.dependency_overrides[get_session] = own_session
    try:
        assert TestClient(app).get("/users/1").json() == {"id": 1, "email": "test@example.com"}
    finally:
        app.dependency_overrides.clear()
```

**The missing user is a bug both sides keep.** `/users/2` answers `500
Internal Server Error` before and after (*lab:* status, headers and body
identical; inside, `ResponseValidationError` before, `LookupError` after).
Typing shows it: without the `if user is None` line, mypy 2.3.1 reports
`Item "None" of "User | None" has no attribute "id"  [union-attr]`. The
line makes the old behaviour explicit and keeps it; a `# type: ignore`
or a `cast` would hide it. The fix is a 404 through a domain error
(`core/errors.md`), a behaviour change in its own commit.

*lab,* Python 3.12.14: `uv run python check_shapes.py L3`, both sides 2
passed; the after is clean under ruff 0.16.9 (`E4,E7,E9,F,B,PLC0415,
TRY002`) and mypy 2.3.1. The override test failed on an after whose
`get_users` opened its own session: the route read the app's database
(`ada@example.com`), and the override was silently unused.

Steps from before to after: `skills/refactoring/recipes/L3-db-model-at-boundary.md`.
