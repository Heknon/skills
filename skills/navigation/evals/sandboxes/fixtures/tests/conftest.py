import pytest


@pytest.fixture
def db_session():
    return {"engine": "sqlite:///:memory:"}
