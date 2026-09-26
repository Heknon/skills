import pytest

from stock import inventory


@pytest.fixture(autouse=True)
def empty_stock():
    inventory._levels.clear()
    inventory._reserved.clear()
    yield
