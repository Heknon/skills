FREE_SHIPPING_FROM = 50.00
STANDARD_SHIPPING = 4.95


def order_total(prices):
    total = 0.0
    for price in prices:
        total += price
    return total


def shipping_cost(prices):
    """Shipping is free for orders from FREE_SHIPPING_FROM upwards."""
    if order_total(prices) > FREE_SHIPPING_FROM:
        return 0.0
    return STANDARD_SHIPPING
