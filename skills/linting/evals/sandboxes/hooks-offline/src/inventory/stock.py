def reserve(stock: dict[str, int], sku: str, qty: int) -> int:
    """Reserve qty of sku and return what is left."""
    left = stock.get(sku, 0) - qty
    if left < 0:
        raise ValueError(f"not enough {sku}")
    stock[sku] = left
    return left
