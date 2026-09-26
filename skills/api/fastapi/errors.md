# Errors in FastAPI: HTTPException, handlers, validation

The contract (problem details, which status) is `core/errors.md`. This
file is how FastAPI produces it. *lab* rows ran on 0.141.1 and 0.118.0
with the same result unless marked.

## What FastAPI sends by default

| Cause | Status | Body (*lab*) | Raised as |
| --- | --- | --- | --- |
| `raise HTTPException(404, "no item 0")` | 404 | `{"detail": "no item 0"}` | `fastapi.HTTPException` |
| a path no route matches | 404 | `{"detail": "Not Found"}` | **`starlette.exceptions.HTTPException`** |
| a known path, another method | 405, `Allow` | `{"detail": "Method Not Allowed"}` | **`starlette.exceptions.HTTPException`** |
| a parameter or body fails validation | 422 | `{"detail": [{"type", "loc", "msg", "input", "ctx"?}]}` | `RequestValidationError` |
| malformed JSON | 422 | `{"detail": [{"type": "json_invalid", "loc": ["body", 9], "msg": "JSON decode error", ...}]}` | `RequestValidationError` |
| the return value fails the response model | 500 | `Internal Server Error` (plain text) | `ResponseValidationError` |
| any other exception | 500 | `Internal Server Error` (plain text) | itself |

`loc` starts with where the value came from: `body`, `query`, `path`,
`header`, `cookie`. The rest is pydantic's path into the value
(`skills/pydantic/core/read-error.md` reads one).

## Handlers: register on Starlette's class

`fastapi.HTTPException` is a subclass of
`starlette.exceptions.HTTPException` (*lab:* `issubclass` is `True`). A
handler catches its class and subclasses, so:

| Handler registered for | Raised 404 | Router's 404 | Router's 405 |
| --- | --- | --- | --- |
| `fastapi.HTTPException` | handled | **not handled** (`application/json`, `{"detail": "Not Found"}`) | **not handled** |
| `starlette.exceptions.HTTPException` | handled | handled | handled, `Allow` kept if you pass `exc.headers` |

*lab,* sandbox problem-details: with the handler on FastAPI's class,
`GET /tickets/99` was `application/problem+json` but `GET /nope`,
`DELETE /tickets/1` and a bad body were `application/json`.

The full set, from `recipes/service/src/orders_api/problems.py`:

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # keep the exception's headers: Allow on a 405, WWW-Authenticate on a 401
    detail = exc.detail if isinstance(exc.detail, str) else None
    return problem(exc.status_code, detail, headers=exc.headers)

async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]} for e in exc.errors()]
    return problem(422, "The request is not valid.", errors=errors)

async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return problem(500)  # never the exception text: it may hold secrets

def install(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_exception_handler(Exception, unhandled)
```

- `problem()` builds the body and returns `JSONResponse(...,
  media_type="application/problem+json")`; run its values through
  `jsonable_encoder`, because `exc.errors()` can hold objects JSON cannot
  encode (a `ValueError` in `ctx`).
- A handler for your own exception class works the same way
  (`@app.exception_handler(OutOfStock)`; *lab:* 409 problem). The class
  itself is the architecture skill's.

## The Exception handler and TestClient

*lab:* with a handler registered for `Exception`, an endpoint raising
`RuntimeError("secret db password in message")`:

- `TestClient(app)` (default `raise_server_exceptions=True`): the test
  **raises** `RuntimeError`; the handler ran, and Starlette's server
  error middleware re-raises so the server logs it.
- `TestClient(app, raise_server_exceptions=False)`: 500 with the
  handler's `application/problem+json` body.

Test 500 handling with `raise_server_exceptions=False`; keep the default
everywhere else so real bugs fail tests loudly.

## Raising 422 yourself

A `pydantic.ValidationError` from your own code inside an endpoint is a
**500**, not a 422 (*lab*). Convert it:

```python
except ValidationError as e:
    raise RequestValidationError(
        [{**err, "loc": ("body", *err["loc"])} for err in e.errors(include_url=False)]
    ) from e
```

Then the 422 handler shapes it like every other validation error. The
same works for a bad value you check by hand (the recipe's invalid
cursor: `loc` `("query", "cursor")`, `type` `"value_error"`).

## Status names

`from fastapi import status` is Starlette's module. On Starlette 1.7.0,
`status.HTTP_422_UNPROCESSABLE_ENTITY` warns
`StarletteDeprecationWarning` (on 0.48.0, `DeprecationWarning`); write
`status.HTTP_422_UNPROCESSABLE_CONTENT` or `422`
(`core/methods-and-status.md`).
