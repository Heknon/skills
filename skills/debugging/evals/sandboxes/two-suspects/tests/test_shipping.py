from shop.shipping import shipping_cost


def test_small_order_pays_shipping():
    assert shipping_cost([10.0, 5.0]) == 4.95


def test_large_order_ships_free():
    assert shipping_cost([40.0, 30.0]) == 0.0
