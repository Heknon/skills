# Responses: models, filtering, status codes

## The response model filters

FastAPI takes the response model from `response_model=` or, when that is
absent, from the return annotation. It validates the return value
against it and sends only the model's fields. *lab, 0.141.1 and 0.118.0*,
a stored record `{"id": 1, "email": "a@x", "password_hash": "h$1"}` and
`UserOut` with `id` and `email`:

| Endpoint | Sent | OpenAPI `schema` |
| --- | --- | --- |
| `def raw(uid)` returning the record, no annotation | **`password_hash` too** | `{}` |
| `def ann(uid) -> UserOut` returning the dict | `{"id":1,"email":"a@x"}` | `$ref UserOut` |
| `-> UserOut` returning a subclass instance that has `password_hash` | `{"id":1,"email":"a@x"}` | `$ref UserOut` |
| `response_model=UserOut` with `-> dict` | filtered | `$ref UserOut` (`response_model` wins) |
| `response_model=None` with `-> dict` | **everything** | no schema |
| `-> UserOut` returning `JSONResponse({...})` | **exactly what the JSONResponse holds**, no filtering | `$ref UserOut`: the document lies |

So: annotate every endpoint with a response model (or set
`response_model`), and do not return a `Response` object from a route
that promises a model. *lab,* sandbox leaky-user: `return
find_member(member_id)` with no annotation sent `password_hash` and
`failed_logins`, and a missing member came back as `200 null`.

Filtering is by the model's fields, not by `extra`: a response model
with `extra="forbid"` given a dict with an extra key fails validation
(*lab:* 500) instead of dropping it. Keep response models on the default
`extra` (`ignore`).

## When the return value is wrong

| Returned | Result (*lab*) |
| --- | --- |
| a dict that fails the model (`{"id": "x"}` for `id: int`) | 500; `ResponseValidationError` with `loc` `('response', 'id')`; TestClient raises it unless `raise_server_exceptions=False` |
| an instance of **another** model class that fails | 500, the same |
| an instance of the response model's **own class**, made invalid with `model_copy(update=...)` | **200 with the invalid data**: not validated again |

The last row is how a PATCH built on `model_copy` stores and returns
`display_name: null` for a field with `min_length=1`
(`core/put-and-patch.md`).

## Status codes and headers

```python
@router.post("", status_code=201)
def create_order(body: OrderIn, store: StoreDep, now: Now, response: Response) -> Order:
    order = store.insert(body.model_dump(), created_at=now)
    response.headers["Location"] = f"/orders/{order['id']}"
    return order
```

- `status_code=` on the decorator sets the success status and the
  OpenAPI entry. *lab:* without it a POST answers 200.
- A `response: Response` parameter lets the endpoint set headers
  (`Location`, `ETag`) and still return a model that is filtered.
- `status_code=204` with `return None`: *lab:* the body was `b''`.
- Errors are raised, not returned: `raise HTTPException(404, "...")`
  (`fastapi/errors.md`).

## Which fields are sent

| Option on the decorator | Effect (*lab* where marked) |
| --- | --- |
| `response_model_exclude_unset=True` | fields the returned model did not set are left out (*lab:* `Opt(a=2)` with `b: int \| None = None` sent `{"a": 2}`) |
| `response_model_exclude_none=True` | fields that are `None` are left out |
| `response_model_by_alias` | default `True`: aliases are used in the JSON |

Leaving fields out makes the response shape vary; clients then need to
treat every field as optional. Prefer sending `null`.

## Documenting other responses

List the error statuses an operation can return so the OpenAPI document
shows them:

```python
@router.get("/{order_id}", responses={404: {"description": "No such order"}})
```

FastAPI adds a `422` entry with the `HTTPValidationError` schema to
every operation that takes parameters or a body (*lab*). When a handler
changes the error shape to problem details, that generated 422 schema no
longer matches what is sent; say so in the API description or override
the entry with `responses={422: {...}}` (*lab:* the given entry replaced
the generated one).
