# L2: business logic in a router

**Rule.** Rules about the domain (prices, limits, allowed state
changes) live in the service, or in the domain model; the route only
translates HTTP to a call and the result back. Signs of logic in a
route: branches on domain state, arithmetic on money, two or more
repositories in one route.

**Why.** A second caller (a worker, a CLI, another route) copies the
rule, and the copies drift. A rule in a route is tested only through
HTTP.

**Target.** A service function or method with the rule, called once by
the route. If the card has no service layer, a plain function in the
feature's module that holds similar rules; never a new layer only for
this (`core/place.md`).

## Before

```python file=before/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
TIERS = {"ada": "gold", "bob": "basic"}


class QuoteIn(BaseModel):
    customer: str
    subtotal_cents: int


@app.post("/quotes")
def quote(body: QuoteIn) -> dict[str, int]:
    total = body.subtotal_cents
    if TIERS.get(body.customer) == "gold" and total >= 10_000:
        total = total * 90 // 100
    return {"total_cents": total}
```

## After

```python file=after/app/pricing.py
TIERS = {"ada": "gold", "bob": "basic"}


def quote_total(customer: str, subtotal_cents: int) -> int:
    """Gold customers get 10% off orders of 100.00 or more."""
    if TIERS.get(customer) == "gold" and subtotal_cents >= 10_000:
        return subtotal_cents * 90 // 100
    return subtotal_cents
```

```python file=after/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel

from app.pricing import quote_total

app = FastAPI()


class QuoteIn(BaseModel):
    customer: str
    subtotal_cents: int


@app.post("/quotes")
def quote(body: QuoteIn) -> dict[str, int]:
    return {"total_cents": quote_total(body.customer, body.subtotal_cents)}
```

## The test both pass

```python file=test_shape.py
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("customer, subtotal, total", [
    ("ada", 10_000, 9_000), ("ada", 9_999, 9_999), ("bob", 10_000, 10_000),
])
def test_quote(customer, subtotal, total):
    r = TestClient(app).post("/quotes", json={"customer": customer, "subtotal_cents": subtotal})
    assert r.json() == {"total_cents": total}
```

After only: the rule without HTTP.

```python file=after/test_pricing.py
from app.pricing import quote_total


def test_gold_threshold():
    assert quote_total("ada", 10_000) == 9_000
```

Checked with `uv run python check_shapes.py L2`.

Steps from before to after: `skills/refactoring/recipes/L2-logic-in-router.md`.
