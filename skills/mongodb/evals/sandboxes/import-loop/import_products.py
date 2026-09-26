"""Nightly import of products.csv (about 200,000 rows) from the ERP.
The file may contain a SKU twice; `sku` has a unique index."""

import csv
import os
import sys

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

db = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"))["catalog"]


def run(path: str) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            doc = {"sku": row["sku"], "name": row["name"], "price_cents": int(row["price_cents"])}
            try:
                db.products.insert_one(doc)
            except DuplicateKeyError:
                pass


if __name__ == "__main__":
    run(sys.argv[1])
