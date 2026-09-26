"""The repository and unit of work against a real database.

SQLite by default (aiosqlite, a file in tmp_path). For PostgreSQL set
DATABASE_URL=postgresql+asyncpg://user:pass@host/db (an empty database).
"""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app.accounts.errors import AccountNotFoundError, DuplicateAccountError
from app.accounts.repository import SqlUnitOfWork
from app.accounts.service import AccountService
from app.db import Base, make_sessionmaker
from app.main import app


@pytest.fixture
def run_db(tmp_path):
    url = os.environ.get(
        "DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'accounts.db'}"
    )

    def run(scenario):
        async def main():
            engine, sessionmaker = make_sessionmaker(url)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            try:
                return await scenario(sessionmaker)
            finally:
                await engine.dispose()

        return asyncio.run(main())

    return run


def test_add_and_get_return_domain_models(run_db):
    async def scenario(sessionmaker):
        async with sessionmaker() as s:
            created = await AccountService(SqlUnitOfWork(s)).open_account(
                "a@example.com", "K1"
            )
        async with sessionmaker() as s:
            return created, await AccountService(SqlUnitOfWork(s)).get(created.id)

    created, read = run_db(scenario)
    assert type(read).__name__ == "Account" and read == created


def test_duplicate_owner_becomes_a_domain_error(run_db):
    async def scenario(sessionmaker):
        async with sessionmaker() as s:
            await AccountService(SqlUnitOfWork(s)).open_account("a@example.com", "K1")
        async with sessionmaker() as s:
            await AccountService(SqlUnitOfWork(s)).open_account("a@example.com", "K2")

    with pytest.raises(DuplicateAccountError) as info:
        run_db(scenario)
    assert type(info.value.__cause__).__name__ == "IntegrityError"


def test_failed_transfer_rolls_back_the_first_write(run_db):
    async def scenario(sessionmaker):
        async with sessionmaker() as s:
            uow = SqlUnitOfWork(s)
            a = await AccountService(uow).open_account("a@example.com", "K1")
            async with uow.transaction():
                await uow.accounts.set_balance(a.id, 10_000)

        async with sessionmaker() as s:
            uow = SqlUnitOfWork(s)
            with pytest.raises(AccountNotFoundError):
                async with uow.transaction():
                    await uow.accounts.set_balance(a.id, 7_500)  # written (flushed) ...
                    await uow.accounts.set_balance(99, 2_500)  # ... then this fails
        async with sessionmaker() as s:
            return await AccountService(SqlUnitOfWork(s)).get(a.id)

    assert run_db(scenario).balance_cents == 10_000


def test_the_wiring_end_to_end(tmp_path, monkeypatch):
    """No override: request -> get_session -> unit of work -> service -> database."""
    if "DATABASE_URL" not in os.environ:
        monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'e2e.db'}")
    monkeypatch.setenv("CREATE_TABLES", "1")
    with TestClient(app) as client:
        body = {"owner_email": "e2e@example.com", "kyc_reference": "K1"}
        assert client.post("/accounts", json=body).status_code == 201
        assert client.post("/accounts", json=body).status_code == 409
        other = {"owner_email": "e2e2@example.com", "kyc_reference": "K2"}
        target = client.post("/accounts", json=other).json()["id"]
        r = client.post(
            "/transfers", json={"source_id": 1, "target_id": target, "amount_cents": 5}
        )
        assert r.json()["code"] == "insufficient_funds"
