"""HTTP mapping, with the service wired to the fake: no database."""

import pytest
from fastapi.testclient import TestClient

from app.accounts.dependencies import get_account_service
from app.accounts.service import AccountService
from app.main import app


@pytest.fixture
def client(uow):
    app.dependency_overrides[get_account_service] = lambda: AccountService(uow)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_open_account_hides_internal_fields(client):
    r = client.post(
        "/accounts", json={"owner_email": "ada@example.com", "kyc_reference": "KYC-1"}
    )
    assert r.status_code == 201
    assert r.json() == {"id": 1, "owner_email": "ada@example.com", "balance_cents": 0}


def test_duplicate_owner_is_409(client):
    body = {"owner_email": "ada@example.com", "kyc_reference": "KYC-1"}
    client.post("/accounts", json=body)
    r = client.post("/accounts", json=body)
    assert r.status_code == 409
    assert r.json() == {
        "code": "duplicate_account",
        "detail": "an account for this owner already exists",
    }


def test_missing_account_is_404(client):
    r = client.get("/accounts/9")
    assert (r.status_code, r.json()["code"]) == (404, "account_not_found")


def test_insufficient_funds_is_409(client):
    client.post(
        "/accounts", json={"owner_email": "a@example.com", "kyc_reference": "K1"}
    )
    client.post(
        "/accounts", json={"owner_email": "b@example.com", "kyc_reference": "K2"}
    )
    r = client.post(
        "/transfers", json={"source_id": 1, "target_id": 2, "amount_cents": 1}
    )
    assert (r.status_code, r.json()["code"]) == (409, "insufficient_funds")


def test_client_cannot_send_a_balance(client):
    r = client.post(
        "/accounts",
        json={
            "owner_email": "a@example.com",
            "kyc_reference": "K1",
            "balance_cents": 1_000_000,
        },
    )
    assert r.status_code == 422
