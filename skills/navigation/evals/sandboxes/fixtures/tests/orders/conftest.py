import pytest


@pytest.fixture
def db_session():
    return {"engine": "sqlite:///orders-fixture.db", "seeded": True}
