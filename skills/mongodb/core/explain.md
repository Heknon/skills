# Explain

**Verdict you produce:** one of three, with the numbers that decide it.

```
query:     <collection, filter, sort, projection, limit>
server:    <version>, <case>, <document count>
plan:      <stages root first, such as LIMIT <- FETCH <- IXSCAN(status_1_created_at_-1)>
numbers:   nReturned <n>, keys <k>, docs <d>, <ms> ms, SORT stage <yes|no>
verdict:   <fine | needs an index | needs a rewrite>, because <the rule below>
```

## 1. Get an explain with numbers

`queryPlanner` shows the plan and no numbers; it cannot give a verdict.
Ask for `executionStats`, which **runs the winning plan to completion**:
on production add a `limit` or do not run it.

mongosh:

```
db.orders.find({status: "paid", total_cents: {$gte: 10000}}).sort({created_at: -1}).limit(20).explain("executionStats")
db.orders.explain("executionStats").aggregate([{$match: {status: "pending"}}, {$group: {_id: "$country", n: {$sum: 1}}}])
```

PyMongo, and saving it for later (`pymongo/explain.md`):

```
uv run --no-sync python <skill>/recipes/explain_report.py --uri "$env:MONGODB_URI" --db shop `
  --find orders --filter '{"status": "paid", "total_cents": {"$gte": 10000}}' `
  --sort '{"created_at": -1}' --limit 20
```

`explain_report.py` prints the plan, the numbers and the verdict of this
file; `--file explain.json` reads a saved one (mongosh:
`EJSON.stringify(<explain>)` into a file). It sends the explain command
and nothing else.

## 2. Read it in this order

1. **`serverInfo.version`**, and how many documents the collection
   holds. An explain on 100 documents says nothing about a million.
2. **The winning plan, root first**: `queryPlanner.winningPlan`, or
   `winningPlan.queryPlan` when `explainVersion` is `'2'` (the
   slot-based engine; *lab*: aggregations with `$group` or a pushed-down
   `$lookup` on 8.0).
3. **The index and its bounds** on each IXSCAN: `indexName`,
   `indexBounds`. A field with `[MinKey, MaxKey]` is not constrained.
4. **`executionStats`**: `nReturned`, `totalKeysExamined`,
   `totalDocsExamined`, `executionTimeMillis`.
5. **A `SORT` stage** anywhere in the plan (SBE: `sort`). Its
   `usedDisk: true` and `spills` mean it overflowed 100 MB.
6. **Rejected plans**: how many candidates the planner raced.

## 3. The rules

| Finding | Rule | Verdict |
| --- | --- | --- |
| COLLSCAN, docs examined far above returned | more than 10 documents read per document returned | needs an index |
| `SORT` stage | no index gives this order | needs an index (sort field in the index, ESR order) |
| IXSCAN, keys examined far above returned | more than 10 keys per document returned: the index does not match (wrong order, missing equality field, range before sort) | needs an index |
| IXSCAN, docs examined far above returned | the FETCH filter drops most documents: filter fields are missing from the index | needs an index |
| bounds `["", {})` next to a regex | an unanchored or case-insensitive `$regex` reads every string key | needs a rewrite (`core/queries.md`) |
| bounds on both sides of one value, `[MinKey, "x")`, `("x", MaxKey]` | the index serves only `$ne`/`$nin`, which reads almost all of it | needs an index on the other predicates |
| `SKIP` with a large `skipAmount` | skip pagination walks every skipped key | needs a rewrite (`core/pagination.md`) |
| EQ_LOOKUP `strategy: 'NestedLoopJoin'`, or `$lookup` with `collectionScans` | no index on the foreign field | needs an index (`core/aggregation.md`) |
| keys = docs = returned, no SORT | the index matches the query | fine |

Ten per returned is a working threshold, not a law: a query that returns
most of a collection may scan it. Say which number decided.

## 4. Real outputs to compare with

*lab, 8.0.32, 1,000,000 orders; query `{status: "paid", total_cents:
{$gte: 10000}}`, sort `{created_at: -1}`, limit 20:*

| Indexes | Plan | Keys | Docs | ms | Verdict |
| --- | --- | --- | --- | --- | --- |
| none | `SORT <- COLLSCAN` | 0 | 1,000,000 | 568 | needs an index |
| `{status:1, total_cents:1, created_at:1}` (range before sort) | `FETCH <- SORT <- IXSCAN` | 188,536 | 20 | 90 | needs an index |
| `{status:1, created_at:1, total_cents:1}` (ESR) | `LIMIT <- FETCH <- IXSCAN` | 20 | 20 | 1 | fine |

The second row fetched only 20 documents because 8.0 sorts the index keys
before FETCH, yet it still read 188,536 keys.

**IXSCAN is not a verdict** (*lab*): with only `{status: 1}`, the query
`{status: {$ne: "shipped"}, country: "BE", "address.city": "Lyon",
total_cents: {$gte: 200000}}` gave

```
winning plan:    FETCH <- IXSCAN
  bounds:        {"status": ["[MinKey, \"shipped\")", "(\"shipped\", MaxKey]"]}
nReturned:       21
keys examined:   399936
docs examined:   399935
time ms:         426
```

With `{country: 1, "address.city": 1, total_cents: 1}`: 35 keys, 35
documents, 21 returned, 1 ms. The 14 extra were shipped orders dropped by
the FETCH filter.

## 5. Aggregations

A pipeline's explain has either one plan (everything pushed into the
query layer) or a `stages` array: the first is `$cursor` with its own
`queryPlanner` and `executionStats`, the others carry `nReturned` and
`executionTimeMillisEstimate`. A `$cursor` that returns 49,951 documents
to stages that cut them to 20 is the finding (`core/aggregation.md`).

## 6. Why a plan won

`allPlansExecution` adds each candidate's trial run
(`executionStats.allPlansExecution`). PyMongo's `Cursor.explain()` uses
it by default (`pymongo/explain.md`). The winner is cached per query
shape: `$planCacheStats` lists the entries (`mongosh/commands.md`).
*lab*: after three runs of one shape with two candidate indexes, one
entry (`isActive: true`, `works: 38`, `createdFromQuery` holding the
filter); creating or dropping any index on the collection emptied the
list. An explain shows the plan for the values you give it; check a
query shape with its common and its rare values.

## Never

- Never call a query efficient from the stage names or from
  `queryPlanner` alone.
- Never quote an explain from mongomock (it has none) or from a toy
  collection as proof.
- Never run `executionStats` without a limit on a large production
  collection.
