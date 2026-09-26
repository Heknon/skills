# L9: a dependency that cannot be swapped

**Rule.** A repository, client or service reaches a route through a
provider function named in `Depends(...)`. Nothing the route uses is
built at module level or inside the route body. Tests swap it with
`app.dependency_overrides[provider]`, never by patching a global
(`core/wiring.md`).

**Why.** A module-level object is shared by every test and every
request; a test must patch the module global and remember where it is
imported. An override keyed by anything but the provider the route
names has no effect: *lab,* sandbox wrong-override: overriding
`NoteRepository` while the route depended on `get_repo` left the real
repository in place, and one test passed only because the real folder
was empty.

**Target.** A provider in the feature's `dependencies.py` (or where the
card keeps providers), `Annotated[..., Depends(provider)]` in the
route, and tests that override that provider and clear the overrides.

## Before

```python file=before/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel


class RateRepository:
    def __init__(self) -> None:
        self.rates = {"EUR": 117, "USD": 127}

    def rate(self, currency: str) -> int:
        return self.rates[currency]


rates = RateRepository()                     # built at import, shared by all
app = FastAPI()


class Price(BaseModel):
    pence: int
    cents: int


@app.get("/convert/{currency}/{pence}")
def convert(currency: str, pence: int) -> Price:
    return Price(pence=pence, cents=pence * rates.rate(currency) // 100)
```

## After

```python file=after/app/main.py
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel


class RateRepository:
    def __init__(self) -> None:
        self.rates = {"EUR": 117, "USD": 127}

    def rate(self, currency: str) -> int:
        return self.rates[currency]


def get_rates() -> RateRepository:
    return RateRepository()


app = FastAPI()


class Price(BaseModel):
    pence: int
    cents: int


@app.get("/convert/{currency}/{pence}")
def convert(currency: str, pence: int,
            rates: Annotated[RateRepository, Depends(get_rates)]) -> Price:
    return Price(pence=pence, cents=pence * rates.rate(currency) // 100)
```

## The test both pass

```python file=test_shape.py
from fastapi.testclient import TestClient

from app.main import app


def test_convert_with_the_real_rates():
    assert TestClient(app).get("/convert/EUR/1000").json() == {"pence": 1000, "cents": 1170}
```

After only: the swap a test needs, by the provider's key.

```python file=after/test_override.py
from fastapi.testclient import TestClient

from app.main import app, get_rates


class FixedRates:
    def rate(self, currency: str) -> int:
        return 200


def test_convert_with_a_fake():
    app.dependency_overrides[get_rates] = FixedRates
    try:
        assert TestClient(app).get("/convert/EUR/10").json()["cents"] == 20
    finally:
        app.dependency_overrides.clear()
```

Checked with `uv run python check_shapes.py L9`.

Steps from before to after: `skills/refactoring/recipes/L9-unswappable-dependency.md`.
