# L4: the service knows HTTP

**Rule.** A service imports nothing from `fastapi` or `starlette`,
raises no `HTTPException`, takes no `Request`, `Response` or
`BackgroundTasks`, and returns no status code. It raises domain errors;
one handler per error category turns them into responses at the edge
(`core/errors.md`).

**Why.** A worker, CLI or test calling the service gets an exception it
cannot handle by type: *lab,* sandbox credit-limit: with
`raise HTTPException(409, ...)` in `OrderService.place`, the nightly
import stopped at the first over-limit row with
`fastapi.exceptions.HTTPException: 409: credit limit exceeded`, because
it catches `AppError`.

**Target.** A domain error in the codebase's errors module under the
right category, raised by the service; one handler per category in the
app factory. The response body stays the same.

## Before

```python file=before/app/main.py
from fastapi import FastAPI, HTTPException

app = FastAPI()
STOCK = {"apple": 3}


class StockService:
    def reserve(self, sku: str, quantity: int) -> int:
        if STOCK.get(sku, 0) < quantity:
            raise HTTPException(409, f"only {STOCK.get(sku, 0)} of {sku} left")
        STOCK[sku] -= quantity
        return STOCK[sku]


@app.post("/reservations/{sku}/{quantity}")
def reserve(sku: str, quantity: int) -> dict[str, int]:
    return {"left": StockService().reserve(sku, quantity)}
```

## After

```python file=after/app/errors.py
class AppError(Exception):
    pass


class ConflictError(AppError):
    pass


class OutOfStockError(ConflictError):
    def __init__(self, sku: str, available: int) -> None:
        super().__init__(sku, available)
        self.sku = sku
        self.available = available

    def __str__(self) -> str:
        return f"only {self.available} of {self.sku} left"
```

```python file=after/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import ConflictError, OutOfStockError

app = FastAPI()
STOCK = {"apple": 3}


class StockService:
    def reserve(self, sku: str, quantity: int) -> int:
        if STOCK.get(sku, 0) < quantity:
            raise OutOfStockError(sku, STOCK.get(sku, 0))
        STOCK[sku] -= quantity
        return STOCK[sku]


@app.exception_handler(ConflictError)
async def conflict(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.post("/reservations/{sku}/{quantity}")
def reserve(sku: str, quantity: int) -> dict[str, int]:
    return {"left": StockService().reserve(sku, quantity)}
```

(In a real layout `StockService` sits in the feature's `service.py`
and the handler in the app factory; one file keeps the shape short.)

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import STOCK, app


def test_reserve_and_conflict():
    STOCK["apple"] = 3
    client = TestClient(app)
    assert client.post("/reservations/apple/2").json() == {"left": 1}
    r = client.post("/reservations/apple/5")
    assert (r.status_code, r.json()) == (409, {"detail": "only 1 of apple left"})
```

After only: a non-HTTP caller handles the error by type.

```python file=after/test_worker_caller.py
import pytest

from app.errors import AppError
from app.main import STOCK, StockService


def test_worker_can_catch_the_domain_error():
    STOCK["pear"] = 0
    with pytest.raises(AppError) as info:
        StockService().reserve("pear", 1)
    assert info.value.available == 0
```

Checked with `uv run python check_shapes.py L4`.

Steps from before to after: `skills/refactoring/recipes/L4-service-knows-http.md`.
