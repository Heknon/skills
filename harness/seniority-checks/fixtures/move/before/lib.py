def total(prices, discount=0):
    return sum(prices) - discount


class Cart:
    def add(self, item, quantity=1):
        return (item, quantity)
