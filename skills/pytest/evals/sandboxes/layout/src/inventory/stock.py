def reserve(stock: dict, sku: str, qty: int) -> dict:
    if stock.get(sku, 0) < qty:
        raise ValueError(f"not enough {sku}")
    return {**stock, sku: stock[sku] - qty}
