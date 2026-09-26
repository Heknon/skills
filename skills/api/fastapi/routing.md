# Routing: routers, order, slashes

Finding the app object and its routes in a repository is the navigation
skill's (`skills/navigation/python/entry-points.md`); this file is how
FastAPI matches a request once you have them. All *lab* rows ran on
FastAPI 0.141.1 and 0.118.0 with the same result.

## APIRouter

```python
router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("")                    # GET /orders
@router.get("/{order_id}")         # GET /orders/{order_id}

app.include_router(router)                  # as declared
app.include_router(router, prefix="/v1")    # GET /v1/orders, GET /v1/orders/{order_id}
```

- `include_router(prefix=...)` adds to the router's own prefix
  (*lab:* `/v1/orders/{order_id}`).
- `tags` group operations in the OpenAPI document; `dependencies=[...]`
  on the router or on `include_router` runs them for every route
  (*lab:* a key check on the include answered 401 before the router's
  own dependency ran; `fastapi/dependencies.md`).
- A route added to a router after `include_router` ran: *lab:* served
  on 0.141.1 (the include keeps a reference to the router), 404 on
  0.118.0 (the routes were copied at include time). Add every route
  before including the router, and the question does not arise.
- Where routers live in a larger codebase (one per resource, how they
  reach services) is the architecture skill's ground.

## Order matters

Routes are tried in the order they were added; the first full match
wins. *lab:* with `@app.get("/users/{user_id}")` (`user_id: int`)
declared before `@app.get("/users/me")`, `GET /users/me` answered 422
`int_parsing` at `['path', 'user_id']`, input `'me'`. Declare fixed paths
before parameter paths, in the same router and across routers.

## Trailing slashes

`redirect_slashes=True` is the default. *lab:*

| Declared | Requested | Answer |
| --- | --- | --- |
| `/items/` | `/items` | 307, `Location: http://testserver/items/` |
| `/things` | `/things/` | 307 to `/things` |
| `/items/` | `POST /items` | 307 (the method is kept on a 307) |
| `/v1/orders` (router `@get("")`) | `/v1/orders/` | 307 to `/v1/orders` |
| `/items/` with `FastAPI(redirect_slashes=False)` | `/items` | 404 |

The `Location` is absolute and built from the request's host; behind a
proxy that does not pass the original host, clients are sent to an
internal name. Declare one form (no trailing slash, `core/naming.md`)
and have clients call it; do not rely on the redirect. TestClient
follows redirects unless `follow_redirects=False`, which hides a
redirect in tests.

## 405 and the Allow header

A path that exists with another method answers 405 with `Allow`. *lab,
both versions:* with `@app.get("/o/{i}")` and `@app.patch("/o/{i}")` as
two routes, `DELETE /o/1` said `Allow: GET` only: Starlette lists the
methods of the first route that matched the path, not all of them. With
one route for both, `@app.api_route("/m/{i}", methods=["GET", "PATCH"])`,
`Allow` listed both. RFC 9110 wants every supported method listed; test
what your API sends before promising it.

HEAD is not added for you: *lab:* `HEAD` on a `@get` route was 405.

## Operation ids

FastAPI generates `operationId` from the function name, the path and
the method: *lab:* `get_user_users__user_id__get`,
`list_orders_v1_orders_get`. Client generators use them as method names,
so renaming an endpoint function changes the generated client: a
breaking change for those clients. To fix them, pass
`operation_id="getOrder"` on the decorator, or
`APIRouter(generate_unique_id_function=...)`.

## Mounting and root path

`app.mount("/static", ...)` serves another ASGI app under a prefix,
outside FastAPI's dependencies and OpenAPI (*lab:* a mounted Starlette
app answered `/static/hi`; no `/static` path in `app.openapi()`). Behind
a reverse proxy that strips a prefix, `FastAPI(root_path="/api")` (or
uvicorn's `--root-path`) makes the docs use it (*lab:* `/docs` then
loaded `/api/openapi.json`). Proxies and ingress
are the deployment skill's ground.
