from shop.parcels import Item, item_count


def test_item_count_adds_quantities() -> None:
    assert item_count([Item("A", 100, 2), Item("B", 250, 3)]) == 5
