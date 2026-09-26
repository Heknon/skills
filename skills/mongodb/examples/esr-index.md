# Worked example: an index for a list endpoint

Kinds: Orient, Explain, Index. MongoDB 8.0.32, PyMongo 4.18.2, the
seeded development database (1,000,000 orders).

## The ask

> `list_orders` is slow on the orders collection. Add an index so it's
> fast. MONGODB_URI points at our development server.

```python
db.orders.find(
    {"country": country, "status": status, "total_cents": {"$gte": min_total_cents}},
    {"_id": 1, "created_at": 1, "total_cents": 1, "status": 1},
).sort("created_at", -1).limit(limit)
```

## Steps

1. **Orient** (`core/orient.md`): `uv run --no-sync python
   <skill>/recipes/orient.py --uri $env:MONGODB_URI --db shop` printed
   `version: 8.0.32`, `replica set rs0`, `orders: ~1,000,000 docs`, and
   one index, `_id_`. The person called it a development server: case
   development.
2. **Explain before** (`core/explain.md`), with the call's real values:
   ```
   uv run --no-sync python <skill>/recipes/explain_report.py --uri $env:MONGODB_URI --db shop `
     --find orders --filter '{"country": "BE", "status": "pending", "total_cents": {"$gte": 100000}}' `
     --sort '{"created_at": -1}' --projection '{"_id": 1, "created_at": 1, "total_cents": 1, "status": 1}' --limit 20
   ```
   ```
   winning plan:    PROJECTION_SIMPLE <- SORT <- COLLSCAN
   nReturned:       20
   keys examined:   0
   docs examined:   1000000
   time ms:         364
   verdict:         needs an index
     - COLLSCAN read 1000000 documents for 20 returned
     - blocking SORT stage: no index gives this order
   ```
3. **Design** (`core/index-design.md`): `country` E, `status` E,
   `created_at` S, `total_cents` R. ESR: `{country: 1, status: 1,
   created_at: -1, total_cents: 1}`. Rejected: one index per field
   (measured in the lab: the planner picked `country_1`, 19,906 keys,
   SORT, 212 ms) and the filter order `{country, status, total_cents,
   created_at}` (a SORT stage).
4. **Create on development**: `db.orders.createIndex({country: 1, status:
   1, created_at: -1, total_cents: 1})` returned
   `country_1_status_1_created_at_-1_total_cents_1`.
5. **Explain after**, same command:
   ```
   winning plan:    LIMIT <- PROJECTION_SIMPLE <- FETCH <- IXSCAN
     index:         country_1_status_1_created_at_-1_total_cents_1
     bounds:        {"country": ["[\"BE\", \"BE\"]"], "status": ["[\"pending\", \"pending\"]"], "created_at": ["[MaxKey, MinKey]"], "total_cents": ["[100000, inf.0]"]}
   nReturned:       20
   keys examined:   81
   docs examined:   20
   time ms:         1
   verdict:         fine
   ```
   81 keys: the index walks `created_at` newest first and skips keys
   whose `total_cents` is below 100,000; no document is fetched for
   them, and no SORT.
6. **Production** (`core/index-live.md`): the README says 40 million
   orders. Prepared, not run: the `createIndexes` command with
   `commitQuorum: "votingMembers"`, as a one-off job before the release,
   watched with `$currentOp`.

## The answer

```
## Result
Index {country: 1, status: 1, created_at: -1, total_cents: 1} for
list_orders (equality, sort, range). Created on the development server.
Production: not created; the command and plan are below for the release
job.

## Checked
- 8.0.32, replica set rs0, development, orders ~1,000,000.
- Before: SORT <- COLLSCAN, 1,000,000 docs for 20 returned, 364 ms.
- After: LIMIT <- FETCH <- IXSCAN on the new index, 81 keys, 20 docs,
  20 returned, 1 ms, no SORT.

## Not checked
- Production build time on 40 million documents: time it on a copy.
- Other queries on orders that might share or conflict with this index:
  searched the repository, only list_orders queries these fields.
```
