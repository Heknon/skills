# Dependencies: Depends, the cache, yield, overrides

The mechanics only. What is injected (a session, a repository, a
service) and how layers are wired and swapped is the architecture
skill's ground; fixtures are the pytest skill's. *lab* rows ran on
FastAPI 0.141.1 and, unless marked, 0.118.0.

## Declaring one

```python
def get_store(request: Request) -> Store:
    return request.app.state.store

StoreDep = Annotated[Store, Depends(get_store)]     # declare once, reuse

@router.get("/{order_id}")
def get_order(order_id: int, store: StoreDep) -> Order: ...
```

- Pass the callable, **not a call**. *lab:* `Depends(get_db())` failed
  when the route was defined, before any request:
  `TypeError: <generator object get_db at 0x...> is not a callable object`
  (for a plain function, the returned value is named instead: `'db' is
  not a callable object`).
- A dependency takes parameters like an endpoint (path, query, header,
  body, other dependencies) and they appear in the OpenAPI document of
  every route that uses it.
- A `def` dependency runs in the threadpool, an `async def` one on the
  event loop (*lab:* thread names `AnyIO worker thread` and the event
  loop's); the rules of `fastapi/concurrency.md` apply to it too.
- `dependencies=[Depends(check)]` on a decorator, router or
  `include_router` runs a dependency whose value is not needed
  (`fastapi/routing.md`).

## One call per request

Within one request, a dependency is called once and its value reused
by everything that asks for it. *lab:* `a` and `b` both depending on
`counter` got the same value, `1`; a third parameter with
`Depends(counter, use_cache=False)` got `2`. So "call it twice to get
two sessions" does not happen unless you say `use_cache=False`. Across
requests nothing is cached; for process-wide values (settings) cache in
the function itself (`functools.lru_cache`) or in `app.state`.

## yield dependencies: setup, teardown, errors

```python
def get_session():
    session = open_session()
    try:
        yield session
        session.commit()          # the endpoint finished without raising
    except Exception:
        session.rollback()        # the endpoint raised, HTTPException included
        raise                     # always re-raise
    finally:
        session.close()
```

*lab,* two such dependencies, one with the default scope and one with
`scope="function"`, around an endpoint:

```
200: request:setup, function:setup, endpoint, function:commit, function:close, request:commit, request:close
404: request:setup, function:setup, endpoint, function:rollback HTTPException, function:close, request:rollback HTTPException, request:close
```

Teardown runs in reverse order of setup, and an exception raised by the
endpoint (an `HTTPException` too) is thrown into each dependency at its
`yield`.

**Swallowing it is an error.** *lab:* a dependency with `except
Exception: pass` around its `yield` (no re-raise) gave a 500, and
TestClient raised `FastAPIError: Response not awaited. There's a high
chance that the application code is raising an exception and a
dependency with yield has a block with a bare except, or a block with
except Exception, and is not raising the exception again.` Log and
re-raise; turn exceptions into responses in handlers
(`fastapi/errors.md`).

## When the code after yield runs: scope

`Depends(..., scope="function" | "request")`, from FastAPI 0.121.0
(*lab:* on 0.118.0, `TypeError: Depends() got an unexpected keyword
argument 'scope'`).

| Scope | Teardown runs | *lab* under uvicorn, teardown sleeps 1 s | *lab*, commit raises after yield |
| --- | --- | --- | --- |
| `"request"` (default) | **after the response is sent** | client had the response in 0.04 s | client got **200**; the error only in the server log |
| `"function"` | after the endpoint returns, **before** the response is sent | client waited 1.01 s | client got **500** |

This changed twice. FastAPI 0.117.1 ran teardown before the response
(*lab:* the client waited 1.08 s, a failing commit gave 500); 0.118.0
moved it after the response (*lab:* 0.04 s, and 200 for a failed
commit); 0.121.0 added `scope="function"` to get the old order back.

So: **a commit that must succeed before the client is told "done" runs
in a `scope="function"` dependency** (or in the endpoint itself). With
the default scope a client can receive 201 for a write that was then
rolled back. Where the unit of work lives is the architecture skill's
decision; this timing is why it matters.

A request-scoped dependency cannot depend on a function-scoped one:
*lab:* `DependencyScopeError: The dependency "req" has a scope of
"request", it cannot depend on dependencies with scope "function".`

## Overrides

`app.dependency_overrides` is a plain `dict` from the original
callable to its replacement. FastAPI looks it up by the **callable
object** named in `Depends(...)`.

| Override key | *lab* result |
| --- | --- |
| the same function object the route uses (`deps.get_store`) | replaced |
| a different function with the same name and body | **not replaced**; the real one ran |
| an `@lru_cache` wrapped dependency, keyed by the wrapper | replaced |
| after `app.dependency_overrides.clear()` | the real one again |

The override is global to the app object: set in one test, it stays for
every later test until cleared. *lab,* sandbox override-leak: a test
that set an override and never cleared it made the next file's test
fail (`'price': None`), pass when run alone, and pass in the reverse
order. Clear in a fixture (`fastapi/testing.md`):

```python
@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
```

Override the dependency the route names, or any sub-dependency: the
lookup happens at every level (*lab:* overriding `leaf`, used by `mid`,
gave `mid(fake-leaf)`). The replacement's own parameters are
resolved as a dependency's are.

## Security dependencies

`HTTPBearer`, `APIKeyHeader` and the other `fastapi.security` classes
are dependencies. Their status for a missing credential changed in
0.122.0: 401 with `WWW-Authenticate`, where earlier releases answered
403 (`fastapi/versions.md`). What to authenticate with is outside this
skill.
