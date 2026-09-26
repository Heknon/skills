"""Order search for the back office."""


def search_orders(db, sku: str, since, page: int, size: int = 25) -> list[dict]:
    cursor = db.orders.find({"items.sku": sku, "created_at": {"$gte": since}}).sort("created_at", -1)
    rows = list(cursor)
    return rows[page * size:(page + 1) * size]
