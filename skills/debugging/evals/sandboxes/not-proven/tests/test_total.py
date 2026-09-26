from billing.total import line_total


def test_line_total():
    assert line_total(3, 1.25) == 3.75


def test_line_total_rounds_half_up():
    assert line_total(1, 10.005) == 10.01
