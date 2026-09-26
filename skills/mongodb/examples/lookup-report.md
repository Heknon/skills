# Worked example: a 45-second report

Kinds: Aggregate, Explain, Index. MongoDB 8.0.32 (and 7.0.43 for
comparison), seeded development data: 200,000 customers, 1,000,000
orders.

## The ask

> report.py takes 45 seconds. Move the `$match` before the `$lookup` so
> it only joins the customers it needs.

```python
PIPELINE = [
    {"$lookup": {"from": "orders", "localField": "_id", "foreignField": "customer_id", "as": "orders"}},
    {"$match": {"country": "BE", "tier": "gold"}},
    {"$project": {"name": 1, "order_count": {"$size": "$orders"}}},
]
```

## Steps

1. **Explain first** (`core/aggregation.md`: the server rewrites
   pipelines):
   ```
   uv run --no-sync python <skill>/recipes/explain_report.py --uri $env:MONGODB_URI --db shop `
     --aggregate customers --pipeline '<the pipeline as JSON>'
   ```
   ```
   explainVersion:  2
   winning plan:    EQ_LOOKUP <- PROJECTION_SIMPLE <- COLLSCAN
     lookup:        shop.orders on customer_id strategy=NestedLoopJoin index=None
   nReturned:       198
   docs examined:   198200000
   time ms:         45285
   verdict:         needs an index
     - $lookup into shop.orders uses NestedLoopJoin: no index on customer_id
   ```
   The raw plan shows the COLLSCAN's `filter` holding `country: 'BE'`
   and `tier: 'gold'`: the server had already moved the `$match` ahead
   of the join. Only 198 customers were joined. Moving the stage by hand
   changes nothing.
2. **The real cost**: `NestedLoopJoin` scans `orders` once per customer:
   198 × 1,000,000 documents.
3. **Index the foreign field** (development):
   `db.orders.createIndex({customer_id: 1})`.
4. **Explain after**:
   ```
   winning plan:    EQ_LOOKUP <- PROJECTION_SIMPLE <- COLLSCAN
     lookup:        shop.orders on customer_id strategy=IndexedLoopJoin index=customer_id_1
   nReturned:       198
   keys examined:   1028
   docs examined:   201028
   time ms:         108
   ```
   1,028 keys are the 198 customers' orders; 200,000 of the documents
   are the COLLSCAN of customers.
5. **What is left**: that COLLSCAN; `{country: 1, tier: 1}` on customers
   would remove it. Offered, not made: 108 ms already met the ask.
6. **Older servers** (`server/versions.md`): on 7.0.43 the same
   pipeline also moved the `$match` first; the join
   showed as a `$lookup` stage with `collectionScans: 198` and took
   62.6 s without the index (`server/versions.md`).

## The answer

```
## Result
The $match was already running before the $lookup: MongoDB moves a $match
on the input's own fields ahead of the join (explain: the COLLSCAN filter
holds country and tier; 198 customers joined). The 45 s came from the join
itself: orders.customer_id had no index, so each of the 198 customers
scanned all 1,000,000 orders (NestedLoopJoin). Added {customer_id: 1} on
orders; the report now takes 108 ms. I left the stage order as it was;
putting $match first is fine for readability but is not the fix.

## Checked
- 8.0.32, development: before 45,285 ms, NestedLoopJoin, 198,200,000
  docs examined; after 108 ms, IndexedLoopJoin on customer_id_1.
- 7.0.43: same $match move; 62.6 s without the index.

## Not checked
- Production: the customer_id index build is a separate step
  (core/index-live.md); not run.
- {country: 1, tier: 1} on customers: proposed, not created.
```
