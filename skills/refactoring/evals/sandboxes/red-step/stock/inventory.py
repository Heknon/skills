"""Stock levels per warehouse, kept in memory by the order service."""

_levels: dict[tuple[str, str], int] = {}
_reserved: dict[tuple[str, str], int] = {}


def receive(warehouse: str, sku: str, quantity: int) -> int:
    key = (warehouse, sku)
    _levels[key] = _levels.get(key, 0) + quantity
    return _levels[key]


def reserve(warehouse: str, sku: str, quantity: int) -> bool:
    key = (warehouse, sku)
    if available(warehouse, sku) < quantity:
        return False
    _reserved[key] = _reserved.get(key, 0) + quantity
    return True


def release(warehouse: str, sku: str, quantity: int) -> None:
    key = (warehouse, sku)
    _reserved[key] = max(0, _reserved.get(key, 0) - quantity)


def available(warehouse: str, sku: str) -> int:
    key = (warehouse, sku)
    return _levels.get(key, 0) - _reserved.get(key, 0)


def total_available(sku: str) -> int:
    warehouses = {warehouse for warehouse, item in _levels if item == sku}
    return sum(available(warehouse, sku) for warehouse in warehouses)
