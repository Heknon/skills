# /// script
# requires-python = ">=3.12"
# dependencies = ["pymongo>=4.11"]
# ///
"""Seed a development database with deterministic shop data.

Same arguments, same documents, on every run: explain output recorded on
one machine can be reproduced on another. Never point it at production;
it drops the collections it seeds.

    uv run seed.py --uri mongodb://localhost:27017/?replicaSet=rs0 --db shop
    uv run seed.py --customers 20000 --orders 100000   # a smaller set

Collections (defaults):
    customers  200,000   name, email (unique), country, tier, created_at
    orders   1,000,000   customer_id, status, country, total_cents,
                         created_at, items[] (multikey), address{}
    events     500,000   device_id, ts, kind, value  (one per reading)
Only the _id index is created: indexes are what the tasks are about.
"""

import argparse
import datetime as dt
import random

from bson import ObjectId
from pymongo import MongoClient

START = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
SPAN = 900 * 24 * 3600  # about 2.5 years of seconds

FIRST = ["Ann", "Bea", "Carl", "Dana", "Emil", "Fay", "Gus", "Hana", "Ivo",
         "Jana", "Karl", "Lena", "Marc", "Nora", "Otto", "Pia", "Rolf", "Sara"]
LAST = ["Lee", "Stone", "Muller", "Martin", "Rossi", "Novak", "Berg",
        "Dubois", "Garcia", "Kowalski", "Jensen", "Moreau", "Weber", "Costa"]
COUNTRIES = ["DE", "FR", "IT", "ES", "PL", "NL", "SE", "PT", "AT", "BE"]
COUNTRY_W = [30, 22, 12, 10, 8, 6, 4, 3, 3, 2]
STATUSES = ["shipped", "paid", "cancelled", "pending"]
STATUS_W = [60, 20, 15, 5]
CITIES = ["Berlin", "Paris", "Rome", "Madrid", "Warsaw", "Lyon", "Munich"]


def oid(seconds: int, n: int) -> ObjectId:
    """An ObjectId from a time and a counter: deterministic, time-ordered."""
    return ObjectId(seconds.to_bytes(4, "big") + n.to_bytes(8, "big"))


def customers(rng: random.Random, count: int):
    for n in range(count):
        s = int(START.timestamp()) + rng.randrange(SPAN)
        first, last = rng.choice(FIRST), rng.choice(LAST)
        # Mixed case on purpose: case-insensitive search is a task.
        name = f"{first} {last}" if n % 3 else f"{first.upper()} {last}"
        yield {
            "_id": oid(s, n),
            "name": name,
            "email": f"{first.lower()}.{last.lower()}.{n}@example.com",
            "country": rng.choices(COUNTRIES, COUNTRY_W)[0],
            "tier": rng.choices(["basic", "silver", "gold"], [80, 15, 5])[0],
            "created_at": dt.datetime.fromtimestamp(s, dt.UTC),
        }


def orders(rng: random.Random, count: int, customer_ids: list[ObjectId]):
    for n in range(count):
        s = int(START.timestamp()) + rng.randrange(SPAN)
        items = [
            {"sku": f"SKU-{rng.randrange(5000):04d}", "qty": rng.randint(1, 4),
             "price_cents": rng.randrange(199, 19999)}
            for _ in range(rng.randint(1, 5))
        ]
        yield {
            "_id": oid(s, n),
            "customer_id": rng.choice(customer_ids),
            "status": rng.choices(STATUSES, STATUS_W)[0],
            "country": rng.choices(COUNTRIES, COUNTRY_W)[0],
            "total_cents": sum(i["qty"] * i["price_cents"] for i in items),
            "created_at": dt.datetime.fromtimestamp(s, dt.UTC),
            "items": items,
            "address": {"street": f"{rng.randint(1, 200)} Main St",
                        "city": rng.choice(CITIES),
                        "zip": f"{rng.randrange(10000, 99999)}"},
        }


def events(rng: random.Random, count: int, devices: int):
    for n in range(count):
        s = int(START.timestamp()) + rng.randrange(SPAN)
        yield {
            "_id": oid(s, n),
            "device_id": f"dev-{rng.randrange(devices):04d}",
            "ts": dt.datetime.fromtimestamp(s, dt.UTC),
            "kind": rng.choices(["temp", "humidity", "door"], [70, 25, 5])[0],
            "value": round(rng.uniform(-10, 40), 2),
        }


def load(coll, docs, batch: int = 10_000) -> int:
    coll.drop()
    buf, total = [], 0
    for doc in docs:
        buf.append(doc)
        if len(buf) == batch:
            total += len(coll.insert_many(buf, ordered=False).inserted_ids)
            buf = []
    if buf:
        total += len(coll.insert_many(buf, ordered=False).inserted_ids)
    return total


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--uri", default="mongodb://localhost:27017/")
    p.add_argument("--db", default="shop")
    p.add_argument("--customers", type=int, default=200_000)
    p.add_argument("--orders", type=int, default=1_000_000)
    p.add_argument("--events", type=int, default=500_000)
    p.add_argument("--devices", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    db = MongoClient(a.uri)[a.db]
    rng = random.Random(a.seed)
    n = load(db.customers, customers(rng, a.customers))
    print(f"customers: {n}")
    ids = db.customers.distinct("_id")
    ids.sort()
    n = load(db.orders, orders(rng, a.orders, ids))
    print(f"orders: {n}")
    n = load(db.events, events(rng, a.events, a.devices))
    print(f"events: {n}")


if __name__ == "__main__":
    main()
