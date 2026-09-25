import pytest

from inventory.stock import reserve


def test_reserve_reduces_stock():
    assert reserve({"a": 3}, "a", 2) == {"a": 1}


def test_reserve_refuses_too_many():
    with pytest.raises(ValueError, match="not enough a"):
        reserve({"a": 1}, "a", 2)
