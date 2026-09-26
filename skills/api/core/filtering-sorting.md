# Filtering and sorting

Conventions for new list endpoints. An existing API keeps its own.

## Filters

| Need | Query | Rule |
| --- | --- | --- |
| equal to | `?status=open` | named after the field it filters |
| any of | `?status=open&status=cancelled` | repeat the parameter; OR within one field |
| several fields | `?status=open&customer=acme` | AND across fields |
| a range | `?created_after=2026-09-01T00:00:00Z&created_before=...` | `_after` exclusive, `_before` exclusive; say so in the description |
| text search | `?q=bolt` | only where the store can serve it (mongodb skill) |

- **Allow list, not pass-through.** Every filter is a declared
  parameter with a type. Never turn arbitrary query keys into a store
  query: that is how a client filters on `password_hash` or sends a
  query operator.
- **Unknown parameters.** By default FastAPI ignores query keys it does
  not declare, so `?stauts=open` silently returns everything (*lab:* a
  route with `status: str | None = None` answered it with 200 and
  `status=None`). A query model with `extra="forbid"` rejects it (*lab*
  below). Choose once for the API; rejecting unknown keys in an API
  that used to ignore them is a breaking change.

## Sorting

- One parameter, `sort`, with an allow list of values; a leading `-`
  means descending: `?sort=-created_at`. Declare the values as a
  `Literal` so an unknown one is a 422 and the choices appear in the
  OpenAPI document.
- The store always appends the unique tie-breaker (id) to whatever the
  client chose, so pages stay stable (`core/pagination.md`). The cursor
  encodes the chosen sort key too; a cursor from one sort used with
  another is a 422.
- Sort only on fields the store can sort efficiently (an index; the
  mongodb skill's ground). A sort that scans the collection is a slow
  endpoint waiting for a large tenant.

## In FastAPI: a query model

*lab, FastAPI 0.141.1 and 0.118.0:*

```python
class OrderFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: list[Literal["open", "cancelled"]] = []
    customer: str | None = None
    sort: Literal["created_at", "-created_at", "total", "-total"] = "-created_at"
    limit: int = Field(default=20, ge=1, le=100)

@app.get("/orders")
def orders(f: Annotated[OrderFilter, Query()]): ...
```

| Query | Result |
| --- | --- |
| `?status=open&status=cancelled&sort=total` | 200, `status=['open', 'cancelled']`, `sort='total'` |
| `?sort=price` | 422 `literal_error` at `['query', 'sort']` |
| `?stauts=open` | 422 `extra_forbidden` at `['query', 'stauts']` |
| `?limit=500` | 422 `less_than_equal` at `['query', 'limit']` |
| none | 200 with every default |

The OpenAPI document lists `status`, `customer`, `sort` and `limit` as
separate query parameters. A single `Literal` parameter works the same:
*lab:* `?sort=x` gave `literal_error`, `Input should be 'created_at' or
'-created_at'`.

A `list[...]` query parameter needs `Query()`: without it FastAPI reads a
list as the **body**, even on a GET (`fastapi/parameters.md`).
