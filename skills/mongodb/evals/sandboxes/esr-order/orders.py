"""Orders listing used by GET /orders?country=&status=&min_total=."""

import os

from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))
db = client["shop"]


def list_orders(country: str, status: str, min_total_cents: int, limit: int = 20) -> list[dict]:
    """Newest orders first."""
    cursor = (
        db.orders.find(
            {"country": country, "status": status, "total_cents": {"$gte": min_total_cents}},
            {"_id": 1, "created_at": 1, "total_cents": 1, "status": 1},
        )
        .sort("created_at", -1)
        .limit(limit)
    )
    return list(cursor)


if __name__ == "__main__":
    for order in list_orders("BE", "pending", 100_000):
        print(order)
