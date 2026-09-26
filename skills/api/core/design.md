# Design an endpoint or a resource

**Verdict you produce:** a contract table, one row per operation, that
a client could code against, and the checks that show the code matches
it.

```
| Method and path | Request | Success | Errors | Notes |
| POST /orders | OrderIn; Idempotency-Key | 201 Order, Location | 409, 422 | retry-safe with key |
checked: app.openapi() shows each row; a TestClient test per status
```

## Steps

1. **Find what exists.** Read the app's OpenAPI document
   (`fastapi/openapi.md`) and the routers around the change. A new
   endpoint follows the API's existing conventions (naming, error
   shape, pagination) unless they break an invariant; then say so
   once (step 8).
2. **Name the resource**, a plural noun, and where it sits: a
   collection (`/orders`), one member (`/orders/{order_id}`), or a sub
   collection when the child cannot exist without the parent
   (`/orders/{order_id}/lines`). `core/naming.md`.
3. **Pick the method for each operation** from what it does to the
   resource (`core/methods-and-status.md`):

   | The client wants to | Method |
   | --- | --- |
   | read, search, list | GET (never changes state) |
   | create a member, server picks the id | POST to the collection |
   | replace a member with a full body | PUT |
   | change some fields | PATCH (`core/put-and-patch.md`) |
   | remove a member | DELETE |
   | an action that is not a field edit (cancel, approve, send) | POST to `/{id}/cancel` with a body for its inputs |

4. **Write the request**: path parameters for identity, query parameters
   for how to read (filters, sort, page), headers for protocol
   (`If-Match`, `Idempotency-Key`), the body for the data. Every body is
   a model with `extra="forbid"` unless the API already ignores unknown
   keys.
5. **Write each response**: the success status and its model, and every
   error status with the condition that causes it. Use the API's error
   shape (`core/errors.md`). A list is a page (`core/pagination.md`).
6. **Decide retries and races.** Is the operation idempotent? If it is a
   POST that creates or charges, add an idempotency key. If two clients
   may edit the same resource, add ETag and `If-Match`
   (`core/idempotency.md`).
7. **Check it is additive** if the API is in use: no renamed or removed
   field, no new required input, no tighter rule on existing input
   (`core/compatibility.md`).
8. **Write the table**, then the code if asked (`fastapi/` files and
   `recipes/service/`), then one test per row of the table: each status
   the table promises is seen in a TestClient run.
9. **Read the result back** from `app.openapi()`: every row appears, the
   body is a `requestBody` and not a query parameter, each response has
   its model.

## A worked table

From `recipes/service/src/orders_api/routes.py`, all rows tested there:

| Method and path | Request | Success | Errors |
| --- | --- | --- | --- |
| `POST /orders` | body `OrderIn`; optional `Idempotency-Key` | 201 `Order`, `Location: /orders/{id}` | 409 key in flight, 422 invalid or key reused with another body |
| `GET /orders` | `limit` 1..100 (20), `cursor` | 200 `{items, next_cursor}` newest first | 422 bad limit or cursor |
| `GET /orders/{order_id}` | | 200 `Order`, `ETag` | 404 |
| `PATCH /orders/{order_id}` | merge patch of `OrderIn`; optional `If-Match` | 200 `Order`, new `ETag` | 404, 409 cancelled or still racing, 412 stale `If-Match`, 422 |
| `POST /orders/{order_id}/cancel` | body `CancelRequest {reason}` | 200 `Order`; a repeat returns the same | 404 |

## Never

- Never design from the handler outwards ("the function returns a
  dict, so the API returns a dict"). The table comes first.
- Never put a verb in a path for plain reads and edits (`/getOrder`,
  `/orders/{id}/update`).
- Never leave an error status out of the table because "it cannot
  happen": a missing record, an invalid body and a race always can.
