import pytest

from calc.ops import div


def test_div():
    assert div(6, 3) == 2


def test_div_float():
    assert div(1, 4) == 0.25


@pytest.mark.xfail(reason="#41: division by zero should return inf")
def test_div_by_zero():
    assert div(1, 0) == float("inf")


@pytest.mark.xfail(reason="#57: rounding")
def test_div_rounding():
    assert div(10, 4) == 2.5


def test_div_negative():
    assert div(-6, 3) == -2
