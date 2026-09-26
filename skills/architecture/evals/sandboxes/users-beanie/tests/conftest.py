import os

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.main import app


@pytest.fixture
def client():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        pytest.skip("set MONGODB_URI to a MongoDB server to run these tests")
    os.environ.setdefault("MONGODB_DB", "users_sandbox_test")
    MongoClient(uri).drop_database(os.environ["MONGODB_DB"])
    with TestClient(app) as c:
        yield c


@pytest.fixture
def ada(client):
    r = client.post("/users", json={"email": "ada@example.com", "display_name": "Ada",
                                    "password": "correct horse"})
    assert r.status_code == 201
    return r.json()
