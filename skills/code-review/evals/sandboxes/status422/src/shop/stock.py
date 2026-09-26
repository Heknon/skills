"""Stock levels, kept in memory for this service."""


class OutOfStock(Exception):
    """Fewer units are left than were asked for."""

    def __init__(self, sku: str, left: int) -> None:
        super().__init__(sku, left)
        self.sku = sku
        self.left = left


STOCK = {"SKU-1": 12, "SKU-2": 0}


def reserve(sku: str, qty: int) -> int:
    """Take qty units of sku; return how many are left."""
    left = STOCK.get(sku, 0)
    if qty > left:
        raise OutOfStock(sku, left)
    STOCK[sku] = left - qty
    return STOCK[sku]
