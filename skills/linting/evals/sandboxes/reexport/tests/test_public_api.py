from shop import Basket, price


def test_plugins_can_import_from_the_package() -> None:
    basket = Basket()
    basket.add(250)
    assert basket.total() == price(250) == "2.50"
