# Testing an API

Running tests, fixtures in general, and mocking are the pytest skill's
(`skills/pytest/core/`). This file is what is particular to FastAPI:
the client, the lifespan, dependency overrides. *lab* rows ran on
FastAPI 0.141.1 with Starlette 1.7.0 and 0.118.0 with Starlette 0.48.0.

## Which HTTP library TestClient needs

`fastapi.testclient.TestClient` is Starlette's. Starlette 1.2.0 and
later import `httpx2` first and fall back to `httpx` (read in
`starlette/testclient.py`, and in every wheel from 1.2.0 to 1.7.0);
earlier releases need `httpx`.

| Installed (Starlette 1.7.0) | Importing TestClient (*lab*) |
| --- | --- |
| `httpx2` | works, silently |
| only `httpx` | works, with `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` |
| neither | `RuntimeError: The starlette.testclient module requires the httpx2 package to be installed.` |

`StarletteDeprecationWarning` is a `UserWarning`, not a
`DeprecationWarning`: pytest shows it, and under `-W error` or
`filterwarnings = ["error"]` the import itself fails (*lab*).
`fastapi[standard]` pulls `httpx<1.0.0`, not `httpx2` (its metadata).
Check what the mirror has with `uv pip show httpx httpx2` and put the
right one in the dev group; with Starlette below 1.2, `httpx`.

## The client fixture

```python
@pytest.fixture
def client() -> Iterator[TestClient]:
    # `with` runs the lifespan: a fresh Store per test, closed afterwards
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()  # an override left behind breaks later tests
```

(`recipes/service/tests/conftest.py`.)

- **`with` is not optional** when the app has a lifespan. *lab:* a
  module-level `client = TestClient(app)` failed every test with
  `AttributeError: 'State' object has no attribute 'pool'`
  (`fastapi/lifespan.md`). Moving setup to import time is not the fix.
- **Clear overrides after every test**, even tests that did not set
  one: the override that leaks comes from somewhere else. *lab,*
  sandbox override-leak: the suite failed, the file alone passed, the
  reverse order passed; the autouse fixture above fixed it.
- One client per test gives each test a fresh lifespan (a fresh
  in-memory store in the recipe). A session-wide client is faster and
  shares state between tests; choose it only when setup is expensive,
  and reset the state yourself.

## Overriding a dependency in a test

```python
@pytest.fixture
def frozen_clock() -> datetime:
    """Every order created in the test gets the same created_at: ties."""
    app.dependency_overrides[get_clock] = lambda: FIXED
    return FIXED
```

Key the override on the same function object the route's `Depends`
names, imported from where it is defined (`fastapi/dependencies.md`).
Give it a lambda that returns the fake, never the fake's class: a
dataclass's fields are read as request parameters and the route
answers 422 (*lab*, `fastapi/dependencies.md`).
What to replace (a repository, a client) is the architecture skill's
decision.

## What TestClient does differently from a server

| Behaviour (*lab*) | Under uvicorn | Under TestClient |
| --- | --- | --- |
| an unhandled exception | 500 | **raised in the test** (default `raise_server_exceptions=True`), even with an `Exception` handler registered |
| background tasks | after the response is sent | before `client.get(...)` returns |
| a trailing slash redirect | a 307 to the client | followed silently unless `follow_redirects=False` |

TestClient's defaults are `raise_server_exceptions=True` and
`follow_redirects=True` (*lab*, its signature). It sends one request at
a time, so a stall cannot be reproduced with it; time it against a
running server (`fastapi/concurrency.md`).

## Async tests

Use them only when the test must await something else as well. The
anyio pytest plugin comes with Starlette: *lab:* a test marked
`@pytest.mark.anyio` ran (on asyncio); an unmarked `async def` test
failed with `async def functions are not natively supported`. The
transport does not run the lifespan; wrap it:

```python
@pytest.mark.anyio
async def test_x():
    async with app.router.lifespan_context(app):
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app),
                                      base_url="http://test") as ac:
            assert (await ac.get("/x")).json() == {"ok": 1}
```

(`httpx.AsyncClient` and `httpx.ASGITransport` have the same names in
httpx 0.28.1.)

## What to assert

- The status **and** the body: `assert r.json() == {...}` for the
  exact shape, so a leaked field fails the test (sandbox leaky-user).
- Every status the contract promises, one test each
  (`core/design.md`).
- For a write: the state after it (GET it again, or read the store),
  and for a retry test, that the side effect happened once.
- Where a parameter is read: send it the way a client will (a JSON body,
  not `?reason=`), and check `app.openapi()` once in a test when the
  place matters (the recipe's `test_openapi_shows_bodies_where_they_belong`).

Then break the endpoint and watch the test fail (SKILL.md invariant 11).
*lab:* each behaviour of the recipe was broken in turn and a test
failed, except removing the override-clearing fixture: in this suite's
order the leaked overrides happened to be harmless, which is why that
fixture is autouse and not left to chance.
