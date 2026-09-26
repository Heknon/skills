"""Proof of each sandbox's planted bug, run inside the sandbox's repository.

    uv run --no-sync python <this file> <sandbox>

Exit 1: the bug shows. Exit 0: it does not (or the feature is not there,
as on main). Exit 125: this proof cannot run here (no MongoDB).
MongoDB proofs read LAB_MONGODB_URL and use their own database, crlab.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MONGO = os.environ.get("LAB_MONGODB_URL")


def client():
    from fastapi.testclient import TestClient
    from shop.api import app

    return app, TestClient(app, raise_server_exceptions=False)


def pagination():
    _, c = client()
    page = c.get("/products", params={"page": 1, "size": 10}).json()
    if len(page) == 25:
        return 0  # main: no paging yet, every product on one page
    seen = set()
    for n in (1, 2, 3):
        seen |= {
            p["sku"] for p in c.get("/products", params={"page": n, "size": 10}).json()
        }
    missing = sorted({f"SKU-{n:03d}" for n in range(1, 26)} - seen)
    print(f"page 1 size 10: {len(page)} items; never shown: {missing}")
    return 1 if missing or len(page) != 10 else 0


def lookup():
    from shop.invoices import invoice_header

    try:
        print(invoice_header("nobody@example.com", 8))
    except AttributeError as exc:
        print(f"invoice_header('nobody@example.com', 8) raised {exc!r}")
        return 1
    return 0


def refunds():
    from datetime import date

    from shop import refunds as r

    if not hasattr(r, "refund_amount"):
        return 0
    got = r.refund_amount(r.Order("o", 4000, date(2026, 3, 1)), date(2026, 3, 10), 50)
    print(f"refund_amount(4000 cents, 50 percent) = {got}")
    return 1 if got != 2000 else 0


def clean():
    _, c = client()
    got = [c.get(u).status_code for u in ("/orders/o-1/total", "/orders/nope/total")]
    if got[0] == 404:
        return 0  # main: no such route yet
    total = c.get("/orders/o-1/total").json()["total_cents"]
    print(f"total of o-1: {total}; unknown order: {got[1]}")
    return 0 if total == 3499 and got[1] == 404 else 1


def status422():
    _, c = client()
    r = c.post("/stock/SKU-1/reserve", json={"qty": 11})
    print(f"qty 11: {r.status_code} {r.json()}")
    return 0 if r.status_code in (200, 409, 422) else 1


def login():
    if not MONGO:
        return 125
    from pymongo import MongoClient
    from shop.api import get_clients

    coll = MongoClient(MONGO)["crlab"]["clients"]
    coll.drop()
    coll.insert_one(
        {"client_id": "acme", "api_key": "s3cret", "scopes": ["orders:read"]}
    )
    app, c = client()
    app.dependency_overrides[get_clients] = lambda: coll
    r = c.post("/auth/scopes", json={"client_id": "acme", "api_key": {"$ne": None}})
    print(f'api_key {{"$ne": null}}: {r.status_code} {r.json()}')
    return 1 if r.status_code == 200 else 0


def users():
    if not MONGO:
        return 125
    os.environ["MONGODB_URL"] = MONGO
    from pymongo import MongoClient

    db = MongoClient(MONGO)["shop"]
    db.users.drop()
    db.users.insert_one(
        {"email": "ann@example.com", "name": "Ann", "password_hash": "h$1"}
    )
    from fastapi.testclient import TestClient
    from shop.api import app

    with TestClient(app) as c:
        r = c.get("/users/by-email/ann@example.com")
    print(f"GET /users/by-email/ann@example.com: {r.status_code} {r.text}")
    return 1 if "password_hash" in r.text else 0


def mocktest():
    work = Path(tempfile.mkdtemp(prefix="cr-mocktest-"))
    try:
        shutil.copytree(Path.cwd() / "src", work / "src")
        shutil.copytree(Path.cwd() / "tests", work / "tests")
        pricing = work / "src" / "shop" / "pricing.py"
        text = pricing.read_text(encoding="utf-8")
        if "def shipping_cents" not in text:
            return 0
        pricing.write_text(text.replace("return cents", "return 0"), encoding="utf-8")
        done = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                str(work / "tests"),
            ],
            cwd=work,
            env={**os.environ, "PYTHONPATH": str(work / "src")},
            capture_output=True,
            text=True,
        )
        print("with shipping_cents broken: " + done.stdout.strip().splitlines()[-1])
        return 1 if done.returncode == 0 else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


def rereview():
    from shop import points

    if not hasattr(points, "transfer_points"):
        return 0
    ann, bob = points.Account("ann", 10), points.Account("bob", 0)
    try:
        points.transfer_points(ann, bob, 10)
    except points.InsufficientPoints:
        print("moving the whole balance of 10 raised InsufficientPoints")
        return 1
    return 0


def counter():
    if not MONGO:
        return 125
    from concurrent.futures import ThreadPoolExecutor

    from pymongo import MongoClient
    from shop.pages import record_view

    pages = MongoClient(MONGO, maxPoolSize=50)["crlab"]["pages"]
    pages.drop()
    pages.insert_one({"slug": "home", "views": 0})
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda _: record_view(pages, "home"), range(2000)))
    views = pages.find_one({"slug": "home"})["views"]
    print(f"2000 views from 16 threads stored as {views}")
    return 1 if views != 2000 else 0


def docstring():
    from shop import parcels

    fn = getattr(parcels, "total_weight_in_grams_of_all_items_in_parcel", None)
    if fn is None:
        return 0
    return 0 if fn([parcels.Item("A", 100, 2)]) == 200 else 1


def defaults():
    from shop.orders import revenue_cents

    got = revenue_cents("c-2")
    print(f"revenue_cents('c-2') = {got}")
    return 1 if got != 1200 else 0


def swallow():
    from shop.api import get_store
    from shop.notes import NoteStore

    class DownStore(NoteStore):
        def add(self, order_id, text):
            raise ConnectionError("database unreachable")

    app, c = client()
    app.dependency_overrides[get_store] = lambda: DownStore()
    r = c.post("/orders/o-1/notes", json={"text": "gift"})
    print(f"store down: {r.status_code} {r.text}")
    return 1 if r.status_code < 300 else 0


def wide():
    import inspect

    from shop.discounts import discounted_cents

    if "order_count" not in inspect.signature(discounted_cents).parameters:
        return 0
    got = discounted_cents(10_000, None, 10)
    print(f"discounted_cents(10000, None, order_count=10) = {got}")
    return 1 if got != 9_500 else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path.cwd() / "src"))
    raise SystemExit(globals()[sys.argv[1]]())
