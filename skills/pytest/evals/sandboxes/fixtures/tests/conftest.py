import pytest


@pytest.fixture
def user():
    return {"name": "ann", "role": "member"}
