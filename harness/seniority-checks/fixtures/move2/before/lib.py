def total(prices, discount=0):
    return sum(prices) - discount


def load(path):
    try:
        with open(path) as handle:
            return handle.read()
    except OSError:
        return None


class Cart:
    def add(self, item, quantity=1):
        return (item, quantity)
