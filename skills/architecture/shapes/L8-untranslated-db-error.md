# L8: a database error untranslated, or translated twice

**Rule.** A driver error (`pymongo.errors.DuplicateKeyError`,
`sqlalchemy.exc.IntegrityError`) is caught in the repository that ran
the statement and re-raised once as a domain error, `from` the
original. The handler maps the domain error's category to a status.
Nothing above the repository imports the driver's errors; nothing in the
repository raises `HTTPException`.

**Why.** Uncaught, a duplicate key is a 500. Caught in the route, every
route and every worker repeats the `try` and imports the driver. Turned
into `HTTPException` in the repository, a worker gets an HTTP error.
Without `from`, the log loses the driver's message (ruff `B904`).

**Target.** `except IntegrityError as exc: raise DuplicateEmailError(email) from exc`
in the repository, at the flush that runs the INSERT; one
`ConflictError` handler. The response stays the same.

## Before

```python file=before/app/main.py
import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)


engine = create_async_engine("sqlite+aiosqlite://")
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
app = FastAPI()


class UserIn(BaseModel):
    email: str


class UserRepository:
    async def add(self, email: str) -> int:
        async with Session() as s, s.begin():
            row = UserRow(email=email)
            s.add(row)
            await s.flush()
            return row.id


@app.post("/users", status_code=201)
async def create_user(body: UserIn) -> dict[str, int]:
    try:
        return {"id": await UserRepository().add(body.email)}
    except IntegrityError as exc:                     # driver error in the route
        raise HTTPException(409, "email already registered") from exc
```

## After

```python file=after/app/main.py
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ConflictError(Exception):
    pass


class DuplicateEmailError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(email)
        self.email = email

    def __str__(self) -> str:
        return "email already registered"


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)


engine = create_async_engine("sqlite+aiosqlite://")
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
app = FastAPI()


@app.exception_handler(ConflictError)
async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=409)


class UserIn(BaseModel):
    email: str


class UserRepository:
    async def add(self, email: str) -> int:
        async with Session() as s, s.begin():
            row = UserRow(email=email)
            s.add(row)
            try:
                await s.flush()
            except IntegrityError as exc:             # translated once, here
                raise DuplicateEmailError(email) from exc
            return row.id


@app.post("/users", status_code=201)
async def create_user(body: UserIn) -> dict[str, int]:
    return {"id": await UserRepository().add(body.email)}
```

(The session per call is kept here only to keep the shape small; a real
repository takes the request's session: see L5.)

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_duplicate_email_is_409():
    client = TestClient(app)
    assert client.post("/users", json={"email": "a@x"}).status_code == 201
    r = client.post("/users", json={"email": "a@x"})
    assert (r.status_code, r.json()) == (409, {"detail": "email already registered"})
```

Checked with `uv run python check_shapes.py L8`. Driver error classes
for each database: `beanie/errors.md`, `sqlalchemy/errors.md`. Steps:
refactoring's recipe `L8`.
