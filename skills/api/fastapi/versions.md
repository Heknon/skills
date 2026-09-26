# FastAPI and Starlette versions

Check first:

```
uv pip show fastapi starlette pydantic httpx httpx2
```

The skill ran on two lines (decision A1): **FastAPI 0.141.1 with
Starlette 1.7.0**, the newest on the index on 2026-09-25, and **FastAPI
0.118.0 with Starlette 0.48.0**, which a team service pins; both with
pydantic 2.13.5 on Python 3.12. Rows marked *lab* were run; "wheel" means
read in the published wheels of every release in between, and
"bisected" means run on the releases around the change.

## What differs

| Topic | 0.118.0 / Starlette 0.48.0 | 0.141.1 / Starlette 1.7.0 | Changed in |
| --- | --- | --- | --- |
| code after `yield` in a dependency | after the response is sent (*lab*) | after the response is sent, by default (*lab*) | 0.118.0 moved it; 0.117.1 ran it before the response (*lab*) |
| `Depends(scope="function" \| "request")` | `TypeError: Depends() got an unexpected keyword argument 'scope'` (*lab*) | works; `"function"` tears down before the response (*lab*) | 0.121.0 (wheel) |
| missing credential with `HTTPBearer`, `APIKeyHeader` | 403 `{"detail": "Not authenticated"}` (*lab*) | 401 with `WWW-Authenticate: Bearer` (or `APIKey`) (*lab*) | 0.122.0 (bisected: 0.121.3 gave 403) |
| body with no `Content-Type` | parsed as JSON (*lab*) | 422 `model_attributes_type` (*lab*); `strict_content_type=False` restores | 0.132.0 (bisected: 0.131.0 parsed it) |
| route added to a router after `include_router` | 404 (*lab*) | served (*lab*) | 0.137.0 (bisected: 0.136.3 gave 404) |
| TestClient's HTTP library | `httpx` | `httpx2`, falling back to `httpx` with a warning (*lab*) | Starlette 1.2.0 (wheel) |
| `status.HTTP_422_UNPROCESSABLE_ENTITY` | 422 with `DeprecationWarning` (*lab*) | 422 with `StarletteDeprecationWarning`, a `UserWarning` (*lab*) | the new name from Starlette 0.48.0; the warning class from 1.3.1 (bisected) |
| `Starlette.on_event` | present | removed from Starlette (wheel, 1.0.0); FastAPI's `on_event` still works, deprecated (*lab*) | Starlette 1.0.0 |
| `ValidationError` schema in the OpenAPI document | `loc`, `msg`, `type` | also `input` and `ctx` (*lab*) | |
| importing TestClient with anyio 4.15.1 | `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated` (*lab*) | no warning | |
| requires Starlette | `>=0.40.0,<0.49.0` (metadata) | `>=0.46.0`, no upper bound (metadata) | upper bound dropped in 0.133.0 (wheel) |
| requires pydantic | `>=1.7.4` (v1 allowed) | `>=2.9.0` | 0.126.0 needs `>=2.7.0`, 0.135.2 `>=2.9.0` (wheel) |

## The same on both (*lab*)

Where parameters come from (the whole matrix in
`fastapi/parameters.md`), response model filtering and the unvalidated
own-class instance, the per-request dependency cache and `use_cache`,
teardown order and the swallowed-exception error, `dependency_overrides`
keys, lifespan with and without `with TestClient`, `on_event` ignored
beside `lifespan=`, handler classes and the router's Starlette
`HTTPException`, the default 422 body, middleware order and CORS
placement, background task order and failure, trailing slash redirects,
the 405 `Allow` header naming only the first route, route order,
operation ids, query models with `extra="forbid"`, `application/*+json`
bodies, the OpenAPI version 3.1.0, and every test of
`recipes/service/` (22 passed on both; on 0.118.0 with `httpx` instead
of `httpx2`).

## Writing for both

- Tear down with the default scope, and commit inside the endpoint (or
  pin 0.121 or later and use `scope="function"`), since the timing
  changed at 0.118.0.
- Do not rely on a security class's 401 or 403; tests that assert one
  of them break across 0.122.0.
- Send `Content-Type: application/json` from every client and test.
- Include routers after all their routes are declared.
- Put `httpx2` in the dev group for Starlette 1.2 and later, `httpx` for
  earlier (`fastapi/testing.md`).
- Write `422` or `HTTP_422_UNPROCESSABLE_CONTENT` (present in both).

## Other releases

For a version not listed, read the installed source rather than
guessing (the offline-docs skill): `fastapi/param_functions.py` for
`Depends`' parameters, `fastapi/routing.py` for body parsing and
`strict_content_type`, `fastapi/security/http.py` for the status codes,
`starlette/testclient.py` for the client library, `starlette/status.py`
for the names.
