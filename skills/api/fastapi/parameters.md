# Where a parameter comes from

FastAPI decides from each endpoint parameter's name, type and marker
whether it is read from the path, the query string, a header, a cookie
or the body. Never guess: the OpenAPI entry says what it decided. Every
row below was run on FastAPI 0.141.1 and 0.118.0 with the same result
(*lab*, the matrix in `/openapi.json`).

## The rules

| Signature | Read from | OpenAPI shows |
| --- | --- | --- |
| a name that appears in the path, `order_id: int` | path | `("order_id", "path", required)` |
| a scalar (`str`, `int`, `float`, `bool`, date types), not in the path | **query**, on every method, POST included | `("reason", "query", required)` |
| `q: str \| None` with no default | query, **required** | `("q", "query", True)`; a request without it is 422 `missing` |
| `q: str \| None = None` | query, optional | `("q", "query", False)` |
| a pydantic model, `item: Item` | body, the whole body is the model | `requestBody` `$ref Item` |
| two models, `item: Item, user: User` | body, **nested under the parameter names** | `Body_d_d_post` with `item` and `user` keys |
| one model with `Body(embed=True)` | body, nested under its name | `{"item": {...}}` |
| a scalar with `Body()` or `Body(embed=True)` | body; `embed` nests it under its name | `Body_...` with `reason` |
| `payload: dict` | body | `object`, `additionalProperties: true` |
| `tags: list[str] = []` with no marker | **body, even on a GET** | `requestBody` array; `?tags=a&tags=b` gives `[]` |
| `tags: Annotated[list[str], Query()] = []` | query, repeated keys | `("tags", "query")`; `?tags=a&tags=b` gives `['a', 'b']` |
| `Annotated[str \| None, Header()] = None` named `x_request_id` | header `x-request-id` (underscores become hyphens) | `("x-request-id", "header")` |
| `Annotated[OrderFilter, Query()]` | query, one parameter per model field | each field as a query parameter (`core/filtering-sorting.md`) |

The two traps these rows show:

- **A plain `str` on a POST is a query parameter.** *lab,* sandbox
  cancel-reason: `def cancel_order(order_id: int, reason: str)` listed
  `('reason', 'query')` and no `requestBody`; posting `{"reason":
  "late"}` gave 422 `missing` at `['query', 'reason']`. A test written
  as `client.post("/orders/1/cancel?reason=late")` passes and hides it.
  Put it in a model (`CancelRequest`) or `Annotated[str,
  Body(embed=True)]`.
- **A second model changes the shape of the first.** With one model the
  body is the model; add a second body parameter and both move under
  their names: *lab:* posting the flat `{"name": "x", "email": "e"}` gave
  `missing` at `['body', 'item']` and `['body', 'user']`. Adding a body
  parameter to an existing endpoint is therefore a breaking change.

## Style

Decision A6 (default): write `Annotated[...]` everywhere; the marker
sits in the type and the default is a normal default.

```python
def list_orders(
    store: StoreDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
    if_match: Annotated[str | None, Header()] = None,
) -> OrderPage:
```

Older code puts the marker in the default:
`q: str | None = Query(default=None, max_length=5)`,
`d: str = Depends(dep)`, `reason: str = Body(embed=True)`. *lab:* this
form still works on both versions with the same OpenAPI entries; read it,
do not rewrite it unasked. ruff's `FAST002` flags it (the linting skill
owns ruff).

Constraints go in the marker (`Query(ge=1, le=100)`, `Path(ge=1)`,
`Header(max_length=200)`) and appear in the OpenAPI document as
`minimum`, `maximum`, `maxLength`. A value outside them is a 422 with
`loc` `['query', 'limit']`: the first element of `loc` names the source.

## The body needs a JSON content type

*lab:* the body is parsed as JSON only when `Content-Type` is
`application/json` or any `application/*+json`
(`application/merge-patch+json` works). Otherwise the model sees the raw
bytes: 422 `model_attributes_type`, `Input should be a valid
dictionary or object to extract fields from`, with the JSON text as
`input`.

| Sent | 0.141.1 | 0.118.0 |
| --- | --- | --- |
| `Content-Type: application/json` | parsed | parsed |
| no `Content-Type` at all | **422** (`strict_content_type=True`, from 0.132.0) | parsed |
| `curl -d '{...}'` (curl sends `application/x-www-form-urlencoded`) | 422 | 422 |
| `curl --json '{...}'`, or `-H "Content-Type: application/json" -d` | parsed | parsed |

`FastAPI(strict_content_type=False)` (also on `APIRouter` and each
route) restores parsing a body with no content type; it does not help
`curl -d`. Calling the app by hand from PowerShell:

```powershell
$body = @{ customer = "acme"; quantity = 2 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/orders -Body $body -ContentType "application/json"

$body | Set-Content body.json
curl.exe --json "@body.json" http://127.0.0.1:8000/orders
```

*lab, PowerShell 7.5.3 on Linux (not run on Windows PowerShell 5.1):*
`Invoke-RestMethod` without `-ContentType` got 422
`model_attributes_type`; with `-ContentType "application/json"` it got
the order back. `curl --json '{"customer": "acme", "quantity": 2}'`
worked in 7.5, and the same with `\"` escapes sent broken JSON (422
`json_invalid`); Windows PowerShell 5.1 passes quotes to native programs
differently, so put the body in a file and send `--json "@body.json"`,
which does not depend on quoting. A body file with a UTF-8 BOM or in
UTF-16 was still parsed (*lab:* 201). In Windows PowerShell 5.1, `curl`
is an alias of `Invoke-WebRequest`; type `curl.exe` (not run on
Windows).

## Check what FastAPI decided

```
uv run --no-sync python <skill>/recipes/tools/openapi_dump.py orders_api.main:app openapi.json
```

then read the operation: `parameters` lists each non-body input with
`in` (`path`, `query`, `header`, `cookie`); `requestBody` is the body.
`fastapi/openapi.md` has more.
