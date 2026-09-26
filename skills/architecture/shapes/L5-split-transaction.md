# L5: a transaction split across layers

**Rule.** One layer owns the transaction of a use case: the service,
through a unit of work it enters explicitly (`core/transactions.md`).
Repositories flush, never commit; routes never commit or roll back; no
repository opens its own session.

**Why.** *lab,* sandbox transfer (SQLAlchemy 2.1.1, aiosqlite): each
repository method committed, so a transfer to a frozen account answered
409 while the debit stayed: `assert 7500 == 10000`. A
`session.rollback()` added in the route changed nothing: the debit was
already committed.

**Target.** Repository methods without `commit()`; a unit of work
holding the session and its repositories; the service wraps the use
case in `async with uow.transaction():`.

## Before

```python file=before/app/bank.py
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[int]


class Accounts:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, account_id: int, delta: int) -> None:
        result = await self.session.execute(
            update(Account).where(Account.id == account_id).values(balance=Account.balance + delta))
        if result.rowcount == 0:
            raise LookupError(account_id)
        await self.session.commit()                      # each write commits


async def transfer(session: AsyncSession, source: int, target: int, amount: int) -> None:
    accounts = Accounts(session)
    await accounts.add(source, -amount)
    await accounts.add(target, amount)
```

## After

```python file=after/app/bank.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[int]


class Accounts:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, account_id: int, delta: int) -> None:
        result = await self.session.execute(
            update(Account).where(Account.id == account_id).values(balance=Account.balance + delta))
        if result.rowcount == 0:
            raise LookupError(account_id)                # no commit here


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts = Accounts(session)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self.session.begin():                 # the one commit or rollback
            yield


async def transfer(session: AsyncSession, source: int, target: int, amount: int) -> None:
    uow = UnitOfWork(session)
    async with uow.transaction():
        await uow.accounts.add(source, -amount)
        await uow.accounts.add(target, amount)
```

## The test both pass

```python file=test_shape.py
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bank import Account, Base, transfer


def run(source, target, amount, tmp_path):
    async def main():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'b.db'}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as s, s.begin():
            s.add_all([Account(id=1, balance=100), Account(id=2, balance=0)])
        failure = None
        async with Session() as s:
            try:
                await transfer(s, source, target, amount)
            except LookupError as e:
                failure = e
        async with Session() as s:
            balances = [(await s.get(Account, i)).balance for i in (1, 2)]
        await engine.dispose()
        return balances, failure
    return asyncio.run(main())


def test_transfer_moves_money(tmp_path):
    assert run(1, 2, 30, tmp_path) == ([70, 30], None)
```

After only: the failure path, which the before gets wrong (a bug, so
not part of the shared test: fix it on purpose, as a behaviour change).

```python file=after/test_rollback.py
from test_shape import run


def test_failed_credit_keeps_the_money(tmp_path):
    balances, failure = run(1, 99, 30, tmp_path)
    assert balances == [100, 0] and isinstance(failure, LookupError)
```

Checked with `uv run python check_shapes.py L5`; the after-only test
fails on the before (`[70, 0]`). Steps: refactoring's recipe `L5`.
