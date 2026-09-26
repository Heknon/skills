# L6: the repository returns raw data

**Rule.** A repository returns domain models (or plain values: an int,
a bool), never a `dict`, a Mongo document with `_id`, a cursor, an
aggregation's rows, a SQLAlchemy `Row`, `Result` or `Select`, or the
collection itself (`get_pymongo_collection()`).

**Why.** Callers index by string keys (`r["_id"]`), so a renamed field or
an aggregation change breaks them at run time, far from the query; the
database's shape leaks into every layer; a type checker sees `dict`.

**Target.** The repository maps each row to a small model named for
what it is (`CustomerTotal`), inside the repository.

## Before

```python file=before/app/main.py
from fastapi import FastAPI

app = FastAPI()
INVOICES = [
    {"customer_id": "c1", "amount_cents": 500, "paid": False},
    {"customer_id": "c1", "amount_cents": 200, "paid": False},
    {"customer_id": "c2", "amount_cents": 900, "paid": True},
]


class InvoiceRepository:
    def open_totals(self) -> list[dict]:
        totals: dict[str, int] = {}
        for inv in INVOICES:
            if not inv["paid"]:
                totals[inv["customer_id"]] = totals.get(inv["customer_id"], 0) + inv["amount_cents"]
        return [{"_id": c, "open_cents": t} for c, t in totals.items()]   # aggregation-shaped rows


@app.get("/open-totals")
def open_totals() -> list[dict]:
    return [{"customer_id": r["_id"], "open_cents": r["open_cents"]}
            for r in InvoiceRepository().open_totals()]
```

## After

```python file=after/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
INVOICES = [
    {"customer_id": "c1", "amount_cents": 500, "paid": False},
    {"customer_id": "c1", "amount_cents": 200, "paid": False},
    {"customer_id": "c2", "amount_cents": 900, "paid": True},
]


class CustomerTotal(BaseModel):              # domain model
    customer_id: str
    open_cents: int


class InvoiceRepository:
    def open_totals(self) -> list[CustomerTotal]:
        totals: dict[str, int] = {}
        for inv in INVOICES:
            if not inv["paid"]:
                totals[inv["customer_id"]] = totals.get(inv["customer_id"], 0) + inv["amount_cents"]
        rows = [{"_id": c, "open_cents": t} for c, t in totals.items()]
        return [CustomerTotal(customer_id=r["_id"], open_cents=r["open_cents"]) for r in rows]


class CustomerTotalOut(BaseModel):           # response schema
    customer_id: str
    open_cents: int


@app.get("/open-totals")
def open_totals() -> list[CustomerTotalOut]:
    return [CustomerTotalOut(**t.model_dump()) for t in InvoiceRepository().open_totals()]
```

The list here stands in for `Invoice.aggregate([...]).to_list()`,
which returns `dict`s keyed by `_id` (the mongodb skill's
`core/aggregation.md`); the mapping line is the same.

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_open_totals():
    assert TestClient(app).get("/open-totals").json() == [{"customer_id": "c1", "open_cents": 700}]
```

Checked with `uv run python check_shapes.py L6`. Steps: refactoring's
recipe `L6`.
