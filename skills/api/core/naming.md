# Naming resources

Rules for new APIs. An existing API keeps its conventions, even odd
ones: consistency inside one API matters more to clients than these
rules, and renaming a path is a breaking change
(`core/compatibility.md`).

## Paths

| Rule | Yes | No |
| --- | --- | --- |
| a noun, plural, for a collection | `/orders` | `/order`, `/orderList` |
| one member by its id | `/orders/{order_id}` | `/orders/get?id=7` |
| the method says what happens | `DELETE /orders/7` | `POST /orders/7/delete`, `GET /deleteOrder` |
| lower case, words joined by hyphens | `/delivery-slots` | `/deliverySlots`, `/delivery_slots` |
| nest only what cannot exist alone, one level | `/orders/{order_id}/lines` | `/customers/{c}/orders/{o}/lines/{l}/notes` |
| an action that is not an edit: a verb under the member, POST | `POST /orders/7/cancel` | `PATCH /orders/7 {"status": "cancelled"}` when cancelling also refunds and notifies |
| no file extensions or formats in the path | `/reports/7` with `Accept` | `/reports/7.json` |
| no trailing slash; pick one form and keep it | `/orders` | both `/orders` and `/orders/` |

RFC 9110 section 9.2.1 on actions in URLs: "If the purpose of such a
resource is to perform an unsafe action, then the resource owner MUST
disable or disallow that action when it is accessed using a safe
request method." A GET that deletes will be run by a crawler, a
prefetcher or a monitoring probe.

**Action or field?** When changing a field has no other effect, it is a
PATCH of that field. When it starts a process (a refund, an email, a
state machine step that some states forbid), it is an action: `POST
/orders/{id}/cancel`, with its inputs (a reason) in a body, and a 409
when the current state forbids it.

## Path parameters

- Name them after the resource: `{order_id}`, not `{id}`, once there is
  more than one level. The FastAPI function parameter has the same name
  (`fastapi/parameters.md`).
- A fixed segment beside a parameter must be declared first:
  `/users/me` before `/users/{user_id}`, or FastAPI matches `me` as an id
  and answers 422 (`fastapi/routing.md`).

## Fields in bodies

- One case style for the whole API; aliases and camelCase output are
  the pydantic skill's (`skills/pydantic/core/serialize.md`).
- Name for what the client sees, not for the database column
  (`quantity`, not `qty_int`). A rename later is breaking.
- Times as RFC 3339 strings in UTC with an offset
  (`2026-09-01T12:00:00Z`); pydantic writes a timezone-aware `datetime`
  this way (*lab:* `created_at: '2026-09-26T05:57:07.028560Z'`).
- Money as an integer of the smallest unit (`amount_cents`) or a
  decimal string, never a float.
- Enumerations as lower-case strings (`"open"`, `"cancelled"`), never
  numbers.

## Query parameters

Lower case, the same style as body fields. The shared ones:
`limit`, `cursor`, `sort`, and filters named after the field they filter
(`status`, `customer`). `core/filtering-sorting.md` and
`core/pagination.md`.
