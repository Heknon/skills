"""The repository and unit of work against a real MongoDB.

Needs MONGODB_URI pointing at a replica set (a single node is enough:
`mongod --replSet rs0`, then `rs.initiate()`); skipped without it.
"""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from pymongo import AsyncMongoClient

from app.accounts.errors import AccountNotFoundError, DuplicateAccountError
from app.accounts.models import AccountDocument
from app.accounts.repository import MongoUnitOfWork
from app.accounts.service import AccountService
from app.db import init_db
from app.main import app

DB = "accounts_recipe_test"


@pytest.fixture
def run_db():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        pytest.skip("set MONGODB_URI to a replica set to run the repository tests")

    def run(scenario):
        async def main():
            await AsyncMongoClient(uri).drop_database(DB)
            client = await init_db(uri, DB, build_indexes=True)  # the unique index
            try:
                return await scenario(client)
            finally:
                await client.close()

        return asyncio.run(main())

    return run


def test_add_and_get_return_domain_models(run_db):
    async def scenario(client):
        service = AccountService(MongoUnitOfWork(client))
        created = await service.open_account("a@example.com", "K1")
        return created, await service.get(created.id)

    created, read = run_db(scenario)
    assert type(read).__name__ == "Account" and read == created


def test_duplicate_owner_becomes_a_domain_error(run_db):
    async def scenario(client):
        service = AccountService(MongoUnitOfWork(client))
        await service.open_account("a@example.com", "K1")
        await service.open_account("a@example.com", "K2")

    with pytest.raises(DuplicateAccountError) as info:
        run_db(scenario)
    assert type(info.value.__cause__).__name__ == "DuplicateKeyError"


def test_malformed_id_is_not_found(run_db):
    async def scenario(client):
        await AccountService(MongoUnitOfWork(client)).get("not-an-id")

    with pytest.raises(AccountNotFoundError):
        run_db(scenario)


def test_failed_transfer_rolls_back_the_first_write(run_db):
    async def scenario(client):
        uow = MongoUnitOfWork(client)
        a = await AccountService(uow).open_account("a@example.com", "K1")
        async with uow.transaction():
            await uow.accounts.set_balance(a.id, 10_000)
        with pytest.raises(AccountNotFoundError):
            async with uow.transaction():
                await uow.accounts.set_balance(a.id, 7_500)  # written ...
                await uow.accounts.set_balance("0" * 24, 2_500)  # ... then this fails
        return await AccountService(uow).get(a.id)

    assert run_db(scenario).balance_cents == 10_000


def test_a_write_without_the_session_escapes_the_transaction(run_db):
    """Why every repository call passes session=: this one does not."""

    async def scenario(client):
        uow = MongoUnitOfWork(client)
        a = await AccountService(uow).open_account("a@example.com", "K1")
        with pytest.raises(RuntimeError):
            async with uow.transaction():
                doc = await AccountDocument.get(a.id)  # no session=
                await doc.set({AccountDocument.balance_cents: 7_500})  # no session=
                msg = "the second write failed"
                raise RuntimeError(msg)
        return await AccountService(uow).get(a.id)

    assert run_db(scenario).balance_cents == 7_500  # not rolled back


def test_the_wiring_end_to_end(run_db, monkeypatch):
    """No override: request -> get_client -> unit of work -> service -> MongoDB."""
    run_db(lambda client: asyncio.sleep(0))  # drops the database, builds the index
    monkeypatch.setenv("MONGODB_DB", DB)
    with TestClient(app) as client:
        body = {"owner_email": "e2e@example.com", "kyc_reference": "K1"}
        source = client.post("/accounts", json=body)
        assert source.status_code == 201
        assert client.post("/accounts", json=body).status_code == 409
        other = {"owner_email": "e2e2@example.com", "kyc_reference": "K2"}
        target = client.post("/accounts", json=other).json()["id"]
        r = client.post(
            "/transfers",
            json={
                "source_id": source.json()["id"],
                "target_id": target,
                "amount_cents": 5,
            },
        )
        assert r.json()["code"] == "insufficient_funds"
