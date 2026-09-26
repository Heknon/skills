# Pagination

Decision A3 (default): **cursor (keyset) pages, the cursor opaque and
built from the sort key plus a unique tie-breaker; offset only for
small lists that do not change while read; always a maximum page
size.** The query and the index behind a keyset page are the mongodb
skill's; this file is the contract.

**Verdict you produce:**

```
order:     <sort fields>, then <unique tie-breaker>, <direction>
page size: default <n>, maximum <m>; above the maximum is a 422
next page: <cursor in body | Link header>; null or absent on the last page
checked:   a test walking every page over ties: <n> rows, each seen once
```

## Why offsets break

With `ORDER BY created_at LIMIT 10 OFFSET 10`, two things go wrong:

1. **Ties.** If ten rows share one `created_at`, the store may return
   them in any order, and a different order for each query. Page 1 and
   page 2 then overlap and some rows are on neither. *lab,* sandbox
   duplicate-rows: walking 40 orders in pages of 10 returned 40 rows,
   38 distinct; ids 10 and 30 never appeared. Adding the id to the sort
   (`(created_at, id)`) made it 40 distinct.
2. **Writes between pages.** A row inserted at the top while a client
   reads page 1 pushes every row down by one: the last row of page 1 is
   the first of page 2. A deleted row does the opposite and a row is
   skipped. A cursor that says "after this key" does not move.

A bigger page size hides both until the list grows. It is not the fix.

## The cursor

- The sort key of the **last row returned**, plus the tie-breaker:
  `(created_at, id)`. The next page is every row strictly after it in
  the sort order.
- **Opaque**: base64 of a small JSON object. Clients pass it back
  unchanged and must not build or parse it; the server may change its
  contents later. A cursor that is just the offset (`cursor=20`) has
  every offset problem.
- **Bad cursor**: a 422, like any other bad parameter (the recipe
  raises `RequestValidationError` with `loc` `["query", "cursor"]`).
- **Last page**: fetch `limit + 1` rows; if the extra row exists there
  is a next page. No count query.

From `recipes/service/src/orders_api/routes.py`:

```python
rows = store.page(limit + 1, after)       # one extra row says whether more exist
items, more = rows[:limit], len(rows) > limit
last = items[-1] if items else None
next_cursor = pages.encode(last["created_at"], last["id"]) if more and last else None
return OrderPage(items=items, next_cursor=next_cursor)
```

## The envelope

```json
{"items": [...], "next_cursor": "eyJ0IjogIjIwMjYtMDktMDFUMTI6MDA6MDArMDA6MDAiLCAiaWQiOiAxNn0"}
```

- `items` and `next_cursor` (`null` on the last page). A client loops
  until `next_cursor` is null.
- Optionally also a `Link` header with `rel="next"` (RFC 8288), which
  generic clients follow: `Link: </orders?cursor=...&limit=10>;
  rel="next"`.
- **No total by default.** A total is a count over the whole filtered
  set on every page; on a large collection it costs more than the page.
  Offer it only when a client needs it, as a separate request or an
  opt-in parameter.

## Page size

- A default (20) and a maximum (100), declared on the parameter so a
  larger value is a 422 and the limits show in the OpenAPI document:
  `limit: Annotated[int, Query(ge=1, le=100)] = 20`. *lab:* `limit=101`
  gave 422 `less_than_equal` at `["query", "limit"]`.
- Raising the maximum is additive; lowering it breaks clients that ask
  for more.

## Changing offset pages to cursors

A response that loses `offset` or a request that loses the `offset`
parameter is breaking (`core/compatibility.md`). Add `cursor` and
`next_cursor` beside the offset fields, fix the order with the
tie-breaker at once (that alone is not breaking), and deprecate
`offset`.

## Test it

Walk every page with a small `limit`, over a set where many rows share
the sort key, and assert each id appears exactly once and in order. Use
a bounded loop so a broken cursor fails instead of hanging. From the
recipe (25 orders created with one frozen `created_at`):

```python
for pages in range(1, 6):                             # bounded: a bad cursor must not hang
    params = {"limit": 10, **({"cursor": cursor} if cursor else {})}
    page = client.get("/orders", params=params).json()
    seen += [o["id"] for o in page["items"]]
    cursor = page["next_cursor"]
    if cursor is None:
        break
assert pages == 3
assert sorted(seen) == sorted(ids)                    # no repeats, none missing
```

*lab:* with the cursor built without the id, or the store's sort
without the id, this test failed; with both, it passed.
