# Writes

**Verdict you produce:** the operation, its write concern, and what a
failure halfway leaves behind.

```
operation:     <insert_many | bulk_write | update_one with operators | upsert | ...>
batch:         <size, ordered or not>
write concern: <default w: majority | stated>
on failure:    <what is stored, what is reported, how a rerun behaves>
checked:       <run on development: time, counts>
```

## 1. Pick the operation

| Need | Operation | Not |
| --- | --- | --- |
| load many new documents | `insert_many(docs, ordered=False)` in batches | `insert_one` in a loop |
| load that may repeat (nightly import) | `bulk_write([UpdateOne(f, {"$set": d}, upsert=True), ...], ordered=False)` | delete all then insert |
| change some fields | `update_one(f, {"$set": {...}})` with dotted paths | `replace_one` of a copy read earlier |
| change a number | `$inc` | read, add in Python, write back |
| add to an array | `$push` (bounded, `core/schema.md`) or `$addToSet` | read, append, write the array |
| change and get the result | `find_one_and_update(..., return_document=ReturnDocument.AFTER)` | update then find |
| a PATCH body | `core/patch-to-set.md` | `$set` of the nested body |

Operators change the stored document in place on the server, so two
writers changing different fields both keep their change. A replace, or a
`$set` of a whole sub-document, writes back everything the writer read,
including what someone else changed since (`beanie/writes.md` shows
Beanie's `save()` doing exactly that).

## 2. One write per round trip is the slow part

*lab, 8.0.32, single-node replica set, default write concern*:

| Load 20,000 documents | Time |
| --- | --- |
| `insert_one` per document | 24.9 s |
| `insert_many`, batches of 1,000, `ordered=False` | 0.21 s |

The nightly-import shape, 200,000 CSV rows with a unique `sku`: a loop of
`insert_one` catching `DuplicateKeyError` stored 20,997 rows of a 21,000
row sample in 27.2 s; batches of 5,000 with `insert_many(ordered=False)`
stored all 200,000 and counted 10 duplicates in 2.19 s. The batched
code is in `pymongo/bulk.md`.

## 3. What a failure leaves behind

*lab*: six inserts where the third and sixth break a unique index:

| `ordered` | Stored | `BulkWriteError.details` |
| --- | --- | --- |
| `True` (default) | the first two; stops at the error | `nInserted: 2`, one `writeErrors` entry at `index: 2`, code 11000 |
| `False` | all but the two duplicates | `nInserted: 4`, entries at `index: 2` and `5` |

Nothing is rolled back in either case. A rerun of an ordered batch
repeats the stored part (duplicates again); an unordered batch of upserts
is safe to rerun. When a batch must be all or nothing, it needs a
transaction (`core/transactions.md`); first ask whether an idempotent
upsert makes that unnecessary.

## 4. Write concern

The default on a replica set is `{w: 'majority', wtimeout: 0}` (*lab*:
`getDefaultRWConcern` returned it with `defaultWriteConcernSource:
'implicit'`). A write returns when most members have it: it survives the
primary's loss. Do not lower it to speed up a loop; batch instead. A
standalone server has no such command (`not supported on standalone
nodes`).

## 5. Upserts

`update_one(filter, update, upsert=True)` inserts `filter`'s equality
fields plus the update when nothing matches. *lab*, 3,000 upserts with
`bulk_write(ordered=False)`: 0.18 s, `matched=5, upserted=2995,
modified=1` (four matched documents already had those values:
`modified` counts real changes only).

Concurrent upserts with the same filter insert duplicates unless the
filter fields have a unique index. *lab*: 300 keys, eight threads each
upserting `{k}` with `$inc`: without an index, 91 keys ended with more
than one document; with a unique index on `k`, none, all 2,400
increments counted, and no `DuplicateKeyError` reached the client.

## Never

- Never write in a loop what one batch can write.
- Never read-modify-write a field the server can change with an operator.
- Never replace a document to change a few fields.
