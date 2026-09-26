# L11: an exception that cannot be handled well

**Rule.** Raise a class a caller can catch by type, never bare
`Exception` (ruff `TRY002`); never make a caller parse `str(e)`. A
custom exception passes its fields to `super().__init__(*fields)` in
the order `__init__` takes them and builds its message in `__str__`
(`placement/custom-errors.md`). Domain errors never subclass
`HTTPException`.

**Why.** `raise Exception("order 7 not found")` can only be caught with
`except Exception`, which also catches every bug; the caller then tests
the message, which breaks when someone rewords it. A class whose
`self.args` does not match its `__init__` cannot be unpickled: *lab*,
Python 3.12.14, sandbox worker-pickle: `TypeError:
QuotaExceededError.__init__() missing 1 required keyword-only argument:
'limit'`, then `BrokenProcessPool`, and the real error was lost.

**Target.** A specific class under the codebase's category, with the
data the handler needs as attributes; callers catch the class.

## Before

```python file=before/app/orders.py
ORDERS = {1: "open"}


def order_status(order_id: int) -> str:
    if order_id not in ORDERS:
        raise Exception(f"order {order_id} not found")
    return ORDERS[order_id]


def status_or_none(order_id: int) -> str | None:
    try:
        return order_status(order_id)
    except Exception as e:
        if "not found" in str(e):              # parses the message
            return None
        raise
```

## After

```python file=after/app/orders.py
ORDERS = {1: "open"}


class NotFoundError(Exception):
    pass


class OrderNotFoundError(NotFoundError):
    code = "order_not_found"

    def __init__(self, order_id: int) -> None:
        super().__init__(order_id)
        self.order_id = order_id

    def __str__(self) -> str:
        return f"order {self.order_id} not found"


def order_status(order_id: int) -> str:
    if order_id not in ORDERS:
        raise OrderNotFoundError(order_id)
    return ORDERS[order_id]


def status_or_none(order_id: int) -> str | None:
    try:
        return order_status(order_id)
    except OrderNotFoundError:
        return None
```

(In a codebase the classes go where its errors live: L10.)

## The test both pass

```python file=test_shape.py
import pytest

from app.orders import order_status, status_or_none


def test_status_or_none():
    assert status_or_none(1) == "open"
    assert status_or_none(7) is None


def test_message_is_kept():
    with pytest.raises(Exception, match="order 7 not found"):
        order_status(7)
```

After only: the error survives a process boundary with its fields.

```python file=after/test_pickle.py
import pickle

from app.orders import OrderNotFoundError


def test_round_trip():
    e = pickle.loads(pickle.dumps(OrderNotFoundError(7)))
    assert (type(e), e.order_id, str(e)) == (OrderNotFoundError, 7, "order 7 not found")
```

Checked with `uv run python check_shapes.py L11`.

Steps from before to after: `skills/refactoring/recipes/L11-unhandleable-exception.md`.
