"""Customer search for the support desk: exact name, any letter case."""

import os
import re

from pymongo import MongoClient

db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))["shop"]


def find_by_name(name: str) -> list[dict]:
    pattern = "^" + re.escape(name) + "$"
    return list(db.customers.find({"name": {"$regex": pattern, "$options": "i"}}, {"name": 1, "email": 1}))
