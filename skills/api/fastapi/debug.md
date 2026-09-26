# Explain what FastAPI did

**Verdict you produce:** the cause, with the evidence that shows it,
and the fix.

```
symptom:  <status and body the client got, or what is missing>
evidence: <the OpenAPI entry | the 422's loc | the handler registered | a source line>
cause:    <one sentence>
fix:      <the change>; checked by <request or test>
```

Start from what the client received, never from the code you expect
ran. Reproduce it with TestClient first (`fastapi/testing.md`), then
follow the symptom's row.

## An unexpected 422

Read `loc`: its first element is where FastAPI looked.

| `loc` and `type` | Cause | Fix |
| --- | --- | --- |
| `['query', 'reason']`, `missing`, while you sent `{"reason": ...}` in the body | a plain scalar parameter is a query parameter | a body model or `Body(embed=True)` (`fastapi/parameters.md`) |
| `['body', 'item']` and `['body', 'user']`, `missing`, for a flat body | two body parameters nest the body under their names | send the nested shape, or one model |
| `['body']`, `model_attributes_type`, `input` is your JSON as text | the body was not read as JSON: no or wrong `Content-Type` (`curl -d`, `Invoke-RestMethod` without `-ContentType`, or none at all on 0.132.0 and later) | send `Content-Type: application/json` |
| `['body', 9]`, `json_invalid` | malformed JSON; the number is the character position | fix the JSON; in PowerShell check the quoting (`fastapi/parameters.md`) |
| `['path', 'user_id']`, `int_parsing`, input `'me'` | `/users/{user_id}` declared before `/users/me` | declare the fixed path first (`fastapi/routing.md`) |
| `['body', 'x']`, `extra_forbidden` | a key the model does not have, with `extra="forbid"` | the client's spelling, or the model |
| `['body']`, `value_error`, from a model validator, on a PATCH | the partial model was validated by FastAPI without the partial context | take the body as a dict and use `apply_patch` (`core/put-and-patch.md`) |
| any, `literal_error` | a value outside the allow list | the error's `msg` lists the allowed values |

Then read the operation in `/openapi.json` to confirm where FastAPI
expects each input.

## A 500 where you expected a 4xx

| Evidence | Cause |
| --- | --- |
| TestClient raises `ResponseValidationError` with `loc` `('response', ...)` | the return value does not fit the response model |
| TestClient raises `pydantic_core._pydantic_core.ValidationError` from your code | a `ValidationError` raised inside the endpoint is not converted; raise `RequestValidationError` (`fastapi/errors.md`) |
| `AttributeError: 'State' object has no attribute ...` | the lifespan did not run (`TestClient` without `with`) or did not set it |
| `FastAPIError: Response not awaited...` | a yield dependency caught the exception and did not re-raise |
| `AttributeError: 'NoneType' object has no attribute ...` inside a validator, on a PATCH | a validator got `None` from the partial model (`skills/pydantic/partial/validators.md`) |

## A field is missing from the response, or an extra one is there

- **Missing**: the response model does not have it; FastAPI dropped it
  (`fastapi/responses.md`). Or `response_model_exclude_unset` /
  `_exclude_none` is set on the decorator.
- **Extra** (a secret went out): the endpoint has no response model
  (`schema: {}` in the OpenAPI entry), has `response_model=None`, or
  returns a `Response` object directly, which is never filtered.

## A handler is not called

| Situation | Cause |
| --- | --- |
| your 404 handler misses unknown paths and 405s | registered for `fastapi.HTTPException`; the router raises Starlette's (`fastapi/errors.md`) |
| a 422 is still `{"detail": [...]}` | no handler for `RequestValidationError` |
| the `Exception` handler "does not run" in a test | it did; TestClient re-raises unless `raise_server_exceptions=False` |
| an `on_event("startup")` function never runs | the app also has `lifespan=`: `on_event` handlers are ignored (`fastapi/lifespan.md`) |
| a dependency override has no effect | the key is not the same function object as in `Depends(...)` |
| a route added to a router does not answer (0.118) | it was added after `include_router` (`fastapi/routing.md`) |

## The page at /docs is blank

The app is fine; the page loads Swagger UI from `cdn.jsdelivr.net`,
which an air-gapped machine cannot reach. Read `/openapi.json`
(`fastapi/openapi.md`).

## When this file has no row

Read the installed source, not the web (the offline-docs skill):
`fastapi/routing.py` (`get_request_handler`: body reading, validation,
the response), `fastapi/dependencies/utils.py` (parameters and
dependencies), `fastapi/exception_handlers.py`, `starlette/routing.py`
(matching, 404, 405). Parameters of `FastAPI`, `APIRouter`, `Query`,
`Body` and `Depends` carry long explanations in `Doc(...)` in
`fastapi/applications.py` and `fastapi/param_functions.py`.
