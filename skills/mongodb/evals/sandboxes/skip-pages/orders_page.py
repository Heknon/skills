"""GET /orders?page=N: the admin order list, newest first, 50 per page."""

import os

from pymongo import MongoClient

db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))["shop"]
PAGE_SIZE = 50


def orders_page(page: int) -> list[dict]:
    return list(
        db.orders.find({}, {"status": 1, "total_cents": 1, "created_at": 1})
        .sort("created_at", -1)
        .skip(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
