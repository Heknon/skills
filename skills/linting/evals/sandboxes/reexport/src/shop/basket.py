from shop.pricing import price


class Basket:
    def __init__(self) -> None:
        self.items: list[int] = []

    def add(self, cents: int) -> None:
        self.items.append(cents)

    def total(self) -> str:
        return price(sum(self.items))
