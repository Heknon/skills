# orders-api: a small complete service

One resource, `/orders`, with each contract rule of this skill in
working code and a test for each. Flat on purpose: where routers,
services and repositories go in a real codebase is the architecture
skill's ground, and the in-memory `Store` stands in for a database whose
queries are the mongodb skill's.

| File | What it shows |
| --- | --- |
| `src/orders_api/main.py` | the app, the lifespan opening and closing the store, handlers installed, the router included |
| `src/orders_api/routes.py` | the contract table in its docstring; POST with `Idempotency-Key`, keyset GET, GET with `ETag`, merge-patch PATCH with `If-Match` and a revision retry, a cancel action |
| `src/orders_api/models.py` | request and response models; the PATCH model from pydantic-partial |
| `src/orders_api/problems.py` | problem details for every error: Starlette's `HTTPException`, `RequestValidationError`, `Exception` |
| `src/orders_api/pages.py` | the opaque cursor: encode, decode, 422 on a bad one |
| `src/orders_api/deps.py` | `get_store` (from `app.state`) and `get_clock` (overridden in tests) |
| `src/orders_api/store.py` | revision on every record, `update_if_revision`, a keyset `page`, idempotency records |
| `src/orders_api/patching.py` | copied unchanged from `skills/pydantic/recipes/patch/src/app/patching.py`; the pydantic skill owns it |
| `tests/conftest.py` | `with TestClient(app)`, overrides cleared after every test, a frozen clock |
| `tests/test_orders.py` | 22 tests, one or more per status in the contract |

## Run it (PowerShell or POSIX)

```
cd recipes/service
uv sync
uv run pytest                                             # 22 passed
uv run uvicorn orders_api.main:app --app-dir src --port 8000
```

On FastAPI 0.118 (Starlette 0.48), TestClient needs `httpx`, not
`httpx2`:

```
uv run --with "fastapi==0.118.0" --with "httpx==0.28.1" pytest   # 22 passed
```

## Checked (*lab*)

- `22 passed` on FastAPI 0.141.1 with Starlette 1.7.0, pydantic 2.13.5,
  pydantic-partial 0.11.1, httpx2 2.13.1, pytest 9.1.1, Python 3.12;
  also with `-W error`. `22 passed, 1 warning` on FastAPI 0.118.0 with
  Starlette 0.48.0 and httpx 0.28.1 (the warning: anyio's
  `BlockingPortal` alias, from Starlette 0.48's test client).
- Under uvicorn 0.54.0: `curl --json '{"customer": "acme", "quantity":
  2}' http://127.0.0.1:8000/orders` gave `HTTP/1.1 201 Created`,
  `location: /orders/1`.
- The tests can fail. Each change below was made alone, and the named
  tests failed:

  | Broken | Failed |
  | --- | --- |
  | handler registered on `fastapi.HTTPException` | `test_unknown_path_and_wrong_method_are_problems` |
  | cursor built without the id | `test_pages_cover_every_order_once_across_ties` |
  | store sorted without the id | the same |
  | `ValidationError` not converted in PATCH | `test_patch_invalid_result_is_422_not_500` |
  | `If-Match` not checked | `test_patch_with_stale_etag_is_412`, `test_if_match_star_and_lists` |
  | one write attempt instead of three | `test_patch_retries_when_another_write_wins` |
  | idempotency key ignored | the three key tests |
  | the 500 handler puts `str(exc)` in `detail` | `test_unhandled_error_is_500_problem_without_the_message` |
  | client fixture without `with` | 18 of 22 |
  | a `model_dump()` merge instead of `apply_patch` | 7 tests |
  | override clearing removed | **none**: the leaked overrides were harmless in this order; the fixture stays autouse (eval override-leak shows the failure it prevents) |

## Use it as a template

Copy the folder, rename the package and the resource, keep the shape:
the contract table in the router's docstring, one test per status,
`with TestClient(app)`, overrides cleared. Replace `Store` with the real
data access (mongodb skill for the queries, architecture skill for where
it lives). Keep the idempotency records in the database with a unique
index on the key, never in process memory, once there is more than one
worker. Delete `.venv` and `uv.lock` if they were created by trying it
out.
