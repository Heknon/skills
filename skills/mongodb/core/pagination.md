# Pagination: the keyset query and its index

**Verdict you produce:** the page query, its index, and proof it costs
the same on every page.

```
sort key:  <(created_at desc, _id desc)>, unique because _id ends it
index:     <{<equality fields>: 1, created_at: -1, _id: -1}>
first:     find(<filter>).sort(<key>).limit(<size>)
next:      filter + $or on the last row's key, same sort and limit
checked:   page <n>: keys <k> for <size> returned; same rows as skip for <m> pages
contract:  the cursor parameter and response shape are the api skill's
```

The api skill owns the contract: the parameter name, how the cursor is
encoded, page size limits and links. This file owns the query and the
index behind them.

## 1. Why skip gets slower

`skip(n)` walks n entries before it returns anything, index or not.
*lab, 8.0.32*, 1,000,000 orders, index `{created_at: -1, _id: -1}`, sort
on the same, 50 per page:

| skip | Plan | Keys | Docs | ms |
| --- | --- | --- | --- | --- |
| 0 | `LIMIT <- FETCH <- IXSCAN` | 50 | 50 | 1 |
| 5,000 | `LIMIT <- FETCH <- SKIP <- IXSCAN` | 5,050 | 50 | 2 |
| 100,000 | same | 100,050 | 50 | 28 |
| 500,000 | same | 500,050 | 50 | 160 |

The index is used and the plan looks fine; the keys grow with the page.
An index cannot fix `skip`. With a filter the index does not cover, SKIP
moves above FETCH and the documents grow too: *lab*, `{status: "paid"}`
on the same index, skip 100,000: `LIMIT <- SKIP <- FETCH <- IXSCAN`,
502,335 keys and 502,335 documents for 50 rows.

## 2. The keyset query

Sort on a key that is unique: the sort field, then `_id`. The next page
starts after the last row of this one:

```python
SORT = [("created_at", -1), ("_id", -1)]

def page(coll, size, after=None, where=None):
    flt = dict(where or {})
    if after is not None:
        t, i = after                      # the previous page's last (created_at, _id)
        flt["$or"] = [{"created_at": {"$lt": t}},
                      {"created_at": t, "_id": {"$lt": i}}]
    return list(coll.find(flt).sort(SORT).limit(size))
```

(`recipes/keyset.py`, with a check against skip.) For ascending order
use `$gt`. With an equality filter (`where={"status": "paid"}`) the index
is `{status: 1, created_at: -1, _id: -1}`: equality first, then the sort
key (ESR).

## 3. Proof

*lab*, the page after 500,000 rows:

```
winning plan:    SUBPLAN <- LIMIT <- FETCH <- SORT_MERGE <- IXSCAN <- IXSCAN
  bounds:        {"created_at": ["(new Date(1742955019000), new Date(-9223372036854775808)]"], "_id": ["[MaxKey, MinKey]"]}
  bounds:        {"created_at": ["[new Date(1742955019000), new Date(1742955019000)]"], "_id": ["(ObjectId('67e3620b000000000000e620'), ObjectId('000000000000000000000000')]"]}
nReturned:       50
keys examined:   50
docs examined:   50
time ms:         1
```

Each `$or` branch is an IXSCAN on the same index, merged in sort order
(SORT_MERGE): no blocking SORT. `recipes/keyset.py --check 2000` walked
2,000 pages both ways: identical rows; page 2,001 cost 50 keys by keyset
and 100,050 keys (30 ms) by skip.

## 4. What changes for the caller

- No "jump to page 500": only next (and previous, by reversing the sort
  and the comparison). If the product needs page numbers, say what they
  cost with the skip numbers above.
- The cursor is the last row's sort key; it stays valid when rows are
  inserted before it. A skip page shifts instead.
- A total count is a separate `count_documents` and costs a scan of the
  matching keys; offer it only if asked.

## Never

- Never "fix" deep pages by adding an index to a `skip` query.
- Never page on a sort key that is not unique: rows with equal keys are
  skipped or repeated at page edges. End the key with `_id`.
