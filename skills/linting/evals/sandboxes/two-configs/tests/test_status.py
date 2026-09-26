from orders.status import is_open


def test_new_order_is_open() -> None:
    assert is_open("new")


def test_shipped_order_is_closed() -> None:
    assert not is_open("shipped")
