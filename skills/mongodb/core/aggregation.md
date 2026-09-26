# Aggregation

**Verdict you produce:** the pipeline, why its stages are in that order,
its explain, and its memory behaviour.

```
pipeline:  <stages>
first:     <$match/$sort/$limit the server runs as a query: index, keys, docs>
joins:     <each $lookup: foreign field, index, strategy>
memory:    <$group/$sort: in memory or spilled (usedDisk, spills)>
explain:   <nReturned per stage, total ms>
verdict:   <fine | needs an index | needs a rewrite>
```

## 1. What the server does with your order

The optimiser rewrites the pipeline before it runs it; the explain shows
the result, and that is what you judge. *lab, 8.0.32*:

- **`$match` on local fields moves ahead of `$lookup`**. `[$lookup
  orders, $match {country: "BE", tier: "gold"}, $project]` on customers
  ran as `EQ_LOOKUP <- PROJECTION_SIMPLE <- COLLSCAN` with the `$match`
  as the COLLSCAN's filter: 198 customers were joined, not 200,000. 7.0.43
  did the same (the `$cursor` stage returned 198).
- **A `$match` moves ahead of stages that do not touch its fields**, even
  `$lookup`, `$unwind` and `$addFields`: Beanie's `fetch_links` pipeline
  (`$lookup` first, `$match {status}` fifth) ran its `$match` as an
  IXSCAN on `status_1` inside `$cursor`.
- **A `$sort` does not move ahead of a `$lookup`.** The same Beanie
  pipeline with `$sort {created_at: -1}` and `$limit 20` after the
  `$lookup` looked up all 49,951 matching orders, then sorted, then kept
  20 (950 ms), even with an index on `{status: 1, created_at: -1}`.
  Written by hand as `[$match, $sort, $limit, $lookup]`: `EQ_LOOKUP <-
  LIMIT <- FETCH <- IXSCAN`, 20 lookups, 2 ms.
- **Unused fields are dropped for you**: `[$match, $unwind: "$items",
  $group by items.sku, ...]` fetched with `PROJECTION_SIMPLE {items: 1,
  _id: 0}` added by the server. A `$project` only to "save memory" early
  in the pipeline is not needed; write one for the output shape.

Write the order that says what you mean anyway ($match, then $sort and
$limit, then joins), and check the explain.

## 2. `$lookup` needs an index on the foreign field

*lab*: the report above, customers joined to their orders on
`orders.customer_id`:

| `orders.customer_id` | Strategy (EQ_LOOKUP) | Docs examined | Time |
| --- | --- | --- | --- |
| no index | `NestedLoopJoin` | 198,200,000 | 45,285 ms |
| `{customer_id: 1}` | `IndexedLoopJoin`, `indexName: 'customer_id_1'` | 201,028 | 108 ms |

A nested loop join scans the foreign collection once per input document.
On 7.0.43, the same join had no EQ_LOOKUP: a separate `$lookup` stage
reported `collectionScans: 198`, `totalDocsExamined: 198000000`, 62.6 s.
The remaining 200,000 documents examined are the COLLSCAN of customers;
`{country: 1, tier: 1}` would remove it.

A join on `_id` (the usual Beanie `Link`) is always indexed. A join whose
input is one document per request is cheap; one inside a report over the
whole collection is not.

## 3. Memory

- **Blocking stages** (`$sort` without an index, `$group`,
  `$setWindowFields`) hold data in memory up to 100 MB each: explain's
  `serverParameters` lists `internalQueryMaxBlockingSortMemoryUsageBytes`,
  `internalDocumentSourceGroupMaxMemoryBytes` and
  `internalDocumentSourceSetWindowFieldsMaxMemoryBytes`, all 104857600 on
  8.0.32.
- **Spilling is on by default**: `allowDiskUseByDefault: true`. The
  explain says `usedDisk: true` and `spills: <n>` on the stage. A spill is
  slow, not an error; `allowDiskUse: false` turns it into an error.
- **`$sort` then `$limit`** is a top-N sort: `limitAmount` in the SORT
  stage; memory for N documents. *lab*: top 10 by `total_cents` over
  1,000,000 orders: `SORT (limitAmount 10) <- COLLSCAN`, 303 ms.
- **One document cannot grow without bound** (*lab*):
  - `$group` with `$push: "$$ROOT"` of 49,951 orders: `BSONObjectTooLarge
    | BSON size limit hit while building Message. Size: 18158876`.
  - `$lookup` joining those orders into one customer: `BSONObjectTooLarge
    | ... BSONObj size: 18158769 (0x11514B1) is invalid. Size must be
    between 0 and 16793600(16MB)`.
  - Past 100 MB they fail earlier, on memory: `ExceededMemoryLimit | ...
    Used too much memory for a single array. Memory limit: 104857600
    bytes`, and `Total size of documents in orders matching pipeline's
    $lookup stage exceeds 104857600 bytes`.

## 4. Pipelines from Python

```python
rows = list(db.customers.aggregate(PIPELINE))                       # PyMongo
db.command("explain", {"aggregate": "customers", "pipeline": PIPELINE, "cursor": {}},
           verbosity="executionStats")
```

`recipes/explain_report.py --aggregate <coll> --pipeline '<json>'` prints
the stages and the verdict. Beanie: raw dict pipelines
(`beanie/queries.md`); Beanie does not check field names inside them.

## Never

- Never move stages around as the fix without the explain before and
  after: the server may already have done it.
- Never ship a `$lookup` whose foreign field has no index unless its
  input is a handful of documents.
