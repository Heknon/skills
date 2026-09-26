# Index cost

**Verdict you produce:** whether an index earns its cost, with the
numbers.

```
index:     <name, spec, size MB>                 ($collStats indexSizes)
serves:    <queries that use it, or "none found in code"; $indexStats ops on every member>
costs:     <writes it slows, its share of the cache>
redundant: <an index it is a prefix of, or none>
verdict:   <keep | replace with <spec> | hide, then drop (core/index-live.md)>
```

## What an index costs

Every insert writes a key to each index (one per element for an array
field). *lab, 8.0.32*, 100,000 small documents inserted in batches of
5,000:

| Secondary indexes | Time | Index size after |
| --- | --- | --- |
| 0 | 0.88 s | 0 MB |
| 3 | 1.56 s | 1.3 MB |
| 6 | 2.27 s | 3.2 MB |

Indexes also take cache: WiredTiger keeps index and document pages in
one cache (*lab*: `serverStatus().wiredTiger.cache["maximum bytes
configured"]` was 7,901,020,160 on a 16 GB machine). When the indexes a
workload uses no longer fit, every query slows, not only the one that
needs the new index.

## Read the sizes

```
db.orders.aggregate([{$collStats: {storageStats: {}}}])   # storageStats.indexSizes, totalIndexSize
```

PyMongo: `next(db.orders.aggregate([{"$collStats": {"storageStats":
{}}}]))["storageStats"]["indexSizes"]`. `recipes/orient.py` prints every
index with its size. *lab*, 1,000,000 orders: data 340 MB, `_id_` 61.7
MB, `customer_id_1` 8.6 MB, `{"items.sku": 1, created_at: 1,
total_cents: 1}` 62.1 MB (multikey: one key per item). The partial
index `pending_by_date` (5% of orders) was 0.6 MB.

## Find the redundant ones

- **A prefix of another index** is redundant for queries: `{status: 1}`
  when `{status: 1, created_at: -1}` exists. Keep it only if it is
  `unique`, partial, has a collation, or is declared by a Beanie model
  (removing it from the model is part of the change).
- **An index no query in the code uses.** Search the code for every
  query on the collection (`core/index-design.md`, step 1), then read
  `$indexStats` on every member (`mongosh/index-stats.md`). Zero ops on
  one member proves nothing.

## Choose between two designs

When a new query could get its own index or share one by reordering an
existing one, prefer the shared one if both queries still show no SORT
and keys near returned in their explains. Two indexes that differ only in
a trailing field are a smell: one of them usually serves both.

## Never

- Never add an index "just in case".
- Never drop an index because its name looks unused or because one
  member's `$indexStats` shows zero (`core/index-live.md`).
