import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Account, Base
from app.main import app


@pytest.fixture
def db_url(tmp_path, monkeypatch):
    url = f"sqlite+aiosqlite:///{tmp_path / 'bank.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    return url


@pytest.fixture
def client(db_url):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def accounts(client, db_url):
    """Three accounts: 1 has 100.00, 2 has 0, 3 is frozen. Returns a balance reader."""
    engine = create_engine(db_url.replace("+aiosqlite", ""))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([Account(id=1, owner="ada", balance_cents=10_000),
                   Account(id=2, owner="bob", balance_cents=0),
                   Account(id=3, owner="cy", balance_cents=0, frozen=True)])
        s.commit()

    def balance(account_id: int) -> int:
        with Session(engine) as s:
            return s.get(Account, account_id).balance_cents

    yield balance
    engine.dispose()
