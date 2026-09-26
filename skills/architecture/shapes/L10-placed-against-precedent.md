# L10: a thing placed against the codebase's precedent

**Rule.** A new exception, constant, enum, helper, type or provider goes
where the codebase already keeps things of its kind at that level
(`placement/place-a-thing.md`). Never a second home for a kind that has
one (`exceptions.py` beside `errors.py`), never a new `utils.py`,
`helpers.py` or `common.py`, never one file per class.

**Why.** The next reader looks for errors in `errors.py` and does not
find this one; the router now imports an error from the service, which
drags the service's imports into every module that handles the error;
the next person copies the new place and the codebase has two
conventions.

**Target.** The definition moves to the file that holds its siblings;
its users import it from there. If the old import path is public, the
refactoring leaves a re-export (refactoring's `steps/move-function.md`).

## Before

```python file=before/app/errors.py
class AppError(Exception):
    pass


class NotFoundError(AppError):
    pass


class CustomerNotFoundError(NotFoundError):
    def __init__(self, customer_id: int) -> None:
        super().__init__(customer_id)
        self.customer_id = customer_id
```

```python file=before/app/service.py
from app.errors import NotFoundError

ORDERS = {1: "open"}


class OrderNotFoundError(NotFoundError):      # defined where it is first raised
    def __init__(self, order_id: int) -> None:
        super().__init__(order_id)
        self.order_id = order_id


def order_status(order_id: int) -> str:
    if order_id not in ORDERS:
        raise OrderNotFoundError(order_id)
    return ORDERS[order_id]
```

```python file=before/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import NotFoundError
from app.service import order_status

app = FastAPI()


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse({"detail": "not found"}, status_code=404)


@app.get("/orders/{order_id}")
def get_status(order_id: int) -> dict[str, str]:
    return {"status": order_status(order_id)}
```

## After

```python file=after/app/errors.py
class AppError(Exception):
    pass


class NotFoundError(AppError):
    pass


class CustomerNotFoundError(NotFoundError):
    def __init__(self, customer_id: int) -> None:
        super().__init__(customer_id)
        self.customer_id = customer_id


class OrderNotFoundError(NotFoundError):
    def __init__(self, order_id: int) -> None:
        super().__init__(order_id)
        self.order_id = order_id
```

```python file=after/app/service.py
from app.errors import OrderNotFoundError

ORDERS = {1: "open"}


def order_status(order_id: int) -> str:
    if order_id not in ORDERS:
        raise OrderNotFoundError(order_id)
    return ORDERS[order_id]
```

```python file=after/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import NotFoundError
from app.service import order_status

app = FastAPI()


@app.exception_handler(NotFoundError)
async def not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse({"detail": "not found"}, status_code=404)


@app.get("/orders/{order_id}")
def get_status(order_id: int) -> dict[str, str]:
    return {"status": order_status(order_id)}
```

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_status_and_404():
    client = TestClient(app)
    assert client.get("/orders/1").json() == {"status": "open"}
    assert client.get("/orders/9").status_code == 404
```

Checked with `uv run python check_shapes.py L10`. The search that
finds this: `checklist/finding.md`, L10. Steps: refactoring's recipe
`L10`.
