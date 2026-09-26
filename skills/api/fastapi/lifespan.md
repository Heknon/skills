# Lifespan and app.state

What the app opens at startup and closes at shutdown: connection pools,
clients, caches. How long a pod waits for shutdown and when probes pass
is the deployment skill's ground.

## Write it

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.store = Store()      # open connections here, not at import time
    yield
    app.state.store.close()        # runs on shutdown, and when a `with TestClient` block ends

app = FastAPI(title="Orders API", version="1.0.0", lifespan=lifespan)
```

Read it in a dependency, not a global (`request.app.state.store`,
`fastapi/dependencies.md`), so tests get a fresh one per client.

The lifespan may also yield a dict; its keys appear on `request.state`
for every request. *lab:* `yield {"pool2": "from-state-dict"}` made
`request.state.pool2` available in endpoints.

## Why not at import time

A pool created at import opens when any module imports the app (a test
collector, a script that dumps the OpenAPI document), is never closed,
and is shared by every test. Keep imports free of side effects; the
lifespan is the one place for them.

## Why not `on_event`

*lab, 0.141.1 and 0.118.0:* `@app.on_event("startup")` still runs, but
warns `DeprecationWarning: on_event is deprecated, use lifespan event
handlers instead.` And when `FastAPI(lifespan=...)` is also given, the
`on_event` handlers are **silently not run**: the log showed the
lifespan's `startup` and `shutdown` and nothing from the `on_event`
function. Starlette 1.0 removed `on_event` from its own `Starlette`
class (read in the 1.0.0 wheel); FastAPI keeps its own copy for now.
Moving to a lifespan: put the startup code before `yield` and the
shutdown code after, in one function, and delete the decorators.

## TestClient runs it only inside `with`

*lab, both versions:*

| Test code | Lifespan | Result |
| --- | --- | --- |
| `client = TestClient(app)` then `client.get(...)` | **not run** | `AttributeError: 'State' object has no attribute 'pool'` (500 with `raise_server_exceptions=False`) |
| `with TestClient(app) as client:` | startup on enter, shutdown on exit | 200; log `['startup', 'shutdown']` |
| httpx `AsyncClient(transport=ASGITransport(app=app))` | **not run** | `AttributeError` on what the lifespan sets |
| the same inside `async with app.router.lifespan_context(app):` | run | 200 |

`fastapi/testing.md` has the fixtures.

## Under a server

uvicorn runs the lifespan once per worker process (*lab,* uvicorn
0.54.0: `--workers 2` printed two startups from two pids), so four
workers open four pools. A lifespan that raises at startup stops the
server before it serves anything: *lab:* `ERROR:    Application startup
failed. Exiting.` and exit code 3. What the orchestrator does on
shutdown (the grace period, SIGTERM) is the deployment skill's ground;
the lifespan's part is to close what it opened after `yield`.
