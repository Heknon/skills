import store


def sum_prices(prices, discount=0):
    return sum(prices) - discount


total = sum_prices
load = store.load


class Cart:
    def add_item(self, item, quantity=1):
        return (item, quantity)

    add = add_item
