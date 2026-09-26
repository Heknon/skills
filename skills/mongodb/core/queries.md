# Queries

**Verdict you produce:** the query, the index it uses, and its explain.

```
query:     <filter, projection, sort, limit, collation>
index:     <name, spec>
explain:   <plan>, keys <k>, docs <d>, returned <n>, <ms> ms
reads:     <what the application receives: fields, count of documents>
```

## 1. Let the server do the work

Each row below was measured on the lab (8.0.32, PyMongo 4.18.2, 1,000,000
orders, index `status_1`):

| Instead of | Write | Lab |
| --- | --- | --- |
| `find()` then filter in Python | the filter in the query | Python filter over all orders: 2.47 s; `count_documents` with the same filter on the server: 0.23 s |
| `len(list(coll.find(q)))` | `coll.count_documents(q)` | 49,951 pending orders: 0.64 s against 0.008 s (`COUNT_SCAN`, 0 documents read) |
| no projection | a projection of the fields the caller uses | 49,951 orders: 0.57 s whole, 0.41 s with `{_id, total_cents}` |
| `count_documents({})` for a dashboard total | `estimated_document_count()` (metadata) | no scan |
| a query per id in a loop | one query with `{"_id": {"$in": ids}}` | `core/aggregation.md`, `beanie/links.md` |

A projection matters most when documents are large or hold arrays the
caller does not read, and it is what makes a covered query possible
(`core/index-design.md`).

## 2. Predicates an index cannot bound

The index is used, but its bounds cover almost everything. Rewrite the
predicate, or index the other fields so this one becomes a filter on few
documents.

| Predicate | Bounds (*lab*) | What to do |
| --- | --- | --- |
| `$regex` without `^` | `["", {})`: every key (200,000 for 14,298 returned) | anchor it, or search words with a text index (`core/index-types.md`) |
| `$regex` with the `i` option, even anchored | `["", {})`: every key (200,000 for 828) | an equality with a collation index, or a stored lower-case field |
| `$regex: "^Ann L"` (anchored, case-sensitive) | `["Ann L", "Ann M")`: 535 keys for 534 | fine |
| `$ne`, `$nin` | `[MinKey, "x")`, `("x", MaxKey]` | index the other predicates; leave `$ne` as a filter |
| `$or` with one clause on an unindexed field | `SUBPLAN <- COLLSCAN` (1,000,000 documents for 68,866) | index every clause: with `status_1` and `country_1`, `OR` of two IXSCANs, 69,857 keys |

For a case-insensitive exact match on 8.0: store the name as is, create
`{name: 1}` with `collation: {locale: "en", strength: 2}`, and query with
the same collation. *lab*: 828 keys for 828 returned.

For a case-insensitive prefix search: store `name_lower` (written by the
application on every write of `name`), index it, and query `{name_lower:
{$regex: "^" + re.escape(prefix.lower())}}`. Case-sensitive and anchored,
it gets tight bounds like the `^Ann L` row. The cost is a second field to
keep in step: every write path must set it.

## 3. Sort and limit

A sort without an index that gives its order is a blocking `SORT`: it
holds the results in memory, up to 100 MB per stage
(`internalQueryMaxBlockingSortMemoryUsageBytes: 104857600`), then spills
to disk. *lab*: sorting all orders by `address.zip` sorted 388 MB,
`usedDisk: true`, 4 spills, 2.3 s; with `.allowDiskUse(false)` it failed:
`Sort exceeded memory limit of 104857600 bytes, but did not opt in to
external sorting.` (`QueryExceededMemoryLimitNoDiskUseAllowed`). With a
`limit`, the SORT keeps only the top N (`limitAmount` in the stage).

Always send the limit to the server (`.limit(n)`); never slice a full
cursor in Python.

## 4. Write it in PyMongo

```python
cursor = (
    db.orders.find(
        {"country": country, "status": status, "total_cents": {"$gte": min_total}},
        {"_id": 1, "created_at": 1, "total_cents": 1},
    )
    .sort([("created_at", -1)])
    .limit(20)
)
```

`sort` takes a key and direction, or a list of pairs for several keys;
`find(filter, projection)`; `.collation({...})` or `collation=` as a
keyword; `.hint("index_name")` only to test a plan, never in production
code. Beanie equivalents: `beanie/queries.md`.

## Never

- Never read a whole collection into Python to filter, count or page it.
- Never call a `$regex` with `i`, an unanchored `$regex`, `$ne` or an
  `$or` with an unindexed clause "indexed" without the bounds in its
  explain.
