# Index design

**Verdict you produce:** the index spec, the queries it serves, and the
explain before and after.

```
queries:   <each query shape it serves: filter fields (eq/range), sort, projection>
index:     <{field: 1, ...}> name <name>, options <none | partial | collation | unique>
serves:    <which queries use it, and as which prefix>
before:    <plan, keys, docs, returned, ms>
after:     <plan, keys, docs, returned, ms>
replaces:  <indexes it makes redundant, to hide then drop (core/index-live.md)>
```

## 1. List the query shapes

From the code, not from the collection: every `find`, `aggregate` and
Beanie query on the collection, with its filter fields, sort and
projection. Mark each filter field **E** (equality, `$eq`, `$in` with few
values), **R** (range: `$gt`, `$lt`, `$gte`, `$lte`, `$ne`, `$nin`,
`$regex`, `$in` with many values) and the sort fields **S**.

## 2. Order the fields: ESR

One compound index per query shape, in this order:

1. **E**quality fields, most selective first when it does not matter
   otherwise (it rarely does for equality).
2. **S**ort fields, in the sort's direction (or all reversed).
3. **R**ange fields.

Why the range goes after the sort: a range on a field before the sort
field gives many index ranges, each sorted on its own, so the server must
sort in memory. *lab, 8.0.32, 1,000,000 orders*, query `{country: "BE",
status: "pending", total_cents: {$gte: 100000}}` sort `{created_at: -1}`
limit 20:

| Index | Plan | Keys | Docs | ms |
| --- | --- | --- | --- | --- |
| one per field (`country_1`, `status_1`, `created_at_1`, `total_cents_1`) | `SORT <- FETCH <- IXSCAN(country_1)`, 4 rejected | 19,906 | 19,906 | 212 |
| `{country:1, status:1, total_cents:1, created_at:-1}` (E R S) | `FETCH <- SORT <- IXSCAN` | 274 | 20 | 2 |
| `{country:1, status:1, created_at:-1, total_cents:1}` (E S R) | `LIMIT <- FETCH <- IXSCAN` | 81 | 20 | 1 |

The ERS index looks close here because only 274 orders match the
equalities and the range together. With a range that matches many (the
same shape with `status: "paid"`, `total_cents >= 10000`: 188,536
matches) ERS read 188,536 keys and ESR read 20. ESR is the default;
measure when a range is very selective and the page is small.

One index per field is not a substitute: the planner picked one of them
(*lab*: `country_1`, four candidates rejected) and filtered and sorted the
rest in memory.

## 3. Serve several queries with one index

An index serves any **prefix** of its fields: `{status: 1, created_at:
-1, _id: -1}` also serves `{status: "paid"}` alone and `{status: "paid"}`
sorted by `created_at`. It does not serve a query on `created_at` alone.
Before adding an index, check whether an existing one is a prefix of the
new one: then the new one replaces it.

Sort direction (*lab*): `{b: 1, d: -1}` served sort `{b: 1, d: -1}` and
`{b: -1, d: 1}` with no SORT; sort `{b: 1, d: 1}` got `SORT <- COLLSCAN`.
A single-field index serves both directions.

## 4. Covered queries

When the projection holds only indexed fields and excludes `_id`, the
server answers from the index. *lab*: index `{status: 1, created_at: -1,
total_cents: 1}`, `find({status: "paid"}, {_id: 0, created_at: 1,
total_cents: 1}).sort({created_at: -1}).limit(20)`:
`LIMIT <- PROJECTION_COVERED <- IXSCAN`, 20 keys, **0 documents**. The
same projection without `_id: 0` gave `PROJECTION_SIMPLE <- FETCH`, 20
documents. A multikey field cannot cover: projecting `items.sku` from
`{"items.sku": 1, total_cents: 1}` fetched 561 documents.

## 5. Arrays (multikey)

An index on a field that is an array in any document is multikey
(`isMultiKey: true`): one key per element. It serves equality on an
element (`{"items.sku": "SKU-0042"}`). A compound index takes at most
one array field per document: *lab*, with `{a: 1, b: 1}`, inserting `{a:
[1, 2], b: [3, 4]}` failed with `cannot index parallel arrays [b] [a]`.
Sorting on a non-array field after it
works: *lab*, `{"items.sku": 1, created_at: -1}` for `{"items.sku":
"SKU-0042", created_at: {$gte: ...}}` sort `{created_at: -1}` limit 25:
25 keys, 25 documents, no SORT.

## 6. Check it

Create it on development data (`core/index-live.md` for production),
run the explain from `core/explain.md` before and after, and quote both.
An index is done when the query's explain shows it, keys and documents
close to `nReturned`, and no SORT stage.

## Never

- Never add one single-field index per filtered field.
- Never say "the index will be used" without the explain after.
- Never add an index without naming the queries it serves; each index
  costs writes and memory (`core/index-cost.md`).
