"""Gold customers in one country with their order count: the key-account report."""

import os
import sys

from pymongo import MongoClient

db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))["shop"]

PIPELINE = [
    {"$lookup": {"from": "orders", "localField": "_id", "foreignField": "customer_id", "as": "orders"}},
    {"$match": {"country": "BE", "tier": "gold"}},
    {"$project": {"name": 1, "order_count": {"$size": "$orders"}}},
]

if __name__ == "__main__":
    for row in db.customers.aggregate(PIPELINE):
        print(row)
    sys.exit(0)
