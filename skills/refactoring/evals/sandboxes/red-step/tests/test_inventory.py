from stock import inventory


def test_receive_and_available():
    inventory.receive("north", "pen", 5)
    assert inventory.available("north", "pen") == 5


def test_reserve_limits_to_available():
    inventory.receive("north", "pen", 2)
    assert inventory.reserve("north", "pen", 2) is True
    assert inventory.reserve("north", "pen", 1) is False


def test_release_never_negative():
    inventory.release("north", "pen", 3)
    assert inventory.available("north", "pen") == 0


def test_total_across_warehouses():
    inventory.receive("north", "pen", 2)
    inventory.receive("south", "pen", 3)
    inventory.reserve("south", "pen", 1)
    assert inventory.total_available("pen") == 4


def test_loaded_levels_are_seen():
    # the nightly import writes levels straight into the table
    inventory._levels[("east", "ink")] = 9
    assert inventory.available("east", "ink") == 9
