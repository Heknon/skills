# Bulk writes and their errors

PyMongo 4.18.2, MongoDB 8.0.32, *lab*. Why batches: `core/writes.md`.

## Batched insert that survives duplicates

The shape that loaded 200,000 CSV rows in 2.19 s (a loop of
`insert_one` managed about 770 rows a second):

```python
from pymongo.errors import BulkWriteError

BATCH = 5_000

def flush(coll, docs, stats):
    try:
        stats["inserted"] += len(coll.insert_many(docs, ordered=False).inserted_ids)
    except BulkWriteError as e:
        stats["inserted"] += e.details["nInserted"]
        for err in e.details["writeErrors"]:
            if err["code"] != 11000:          # only duplicates are expected
                raise
            stats["duplicates"] += 1
```

Call `flush` every `BATCH` rows and once at the end.
`ordered=False` lets the server try every document; the error lists the
failures and the batch's other documents are stored.

## `BulkWriteError.details`

*lab*, keys: `['nInserted', 'nMatched', 'nModified', 'nRemoved',
'nUpserted', 'upserted', 'writeConcernErrors', 'writeErrors']`. Each
`writeErrors` entry has `index` (position in the batch), `code` (11000
for a duplicate key), `errmsg` (`E11000 duplicate key error collection:
lab.imp index: sku_1 ...`) and the failing operation. A non-empty
`writeConcernErrors` means the writes happened but were not confirmed by
the requested number of members.

## Upserts and mixed operations

```python
from pymongo import UpdateOne, InsertOne, DeleteOne

ops = [UpdateOne({"sku": r["sku"]}, {"$set": r}, upsert=True) for r in rows]
res = coll.bulk_write(ops, ordered=False)
res.matched_count, res.upserted_count, res.modified_count
```

*lab*: 3,000 upserts in 0.18 s. Re-running the same batch is safe: it
matches instead of inserting. Give the upsert key a unique index
(`core/writes.md`, concurrent upserts).

## Across collections: `MongoClient.bulk_write` (server 8.0+)

PyMongo 4.9+ has a client-level `bulk_write`; its docstring says
"requires MongoDB server version 8.0+". Operations name their namespace:

```python
res = client.bulk_write([
    InsertOne(namespace="lab.imp2", document={"x": 1}),
    UpdateOne(namespace="lab.imp", filter={"sku": "S00001"}, update={"$inc": {"qty": 1}}),
])
```

*lab*: `inserted_count 1, modified_count 1`. A failure raises
`ClientBulkWriteException`, not `BulkWriteError`; its `write_errors`
entries hold `idx`, `code` (11000), `errmsg`, `keyPattern`, `keyValue`.
One command for several collections; it is not a transaction.

## Batch size

Batches of 1,000 to 10,000 documents worked in the lab. The driver
splits a larger one to fit the server's limits (`hello` reports
`maxMessageSizeBytes: 48000000`, `maxWriteBatchSize: 100000`): *lab*,
one `insert_many` of 150,000 documents of 1 KB went as 4 `insert`
commands. Batch in your code anyway, to bound memory on the client and
to report progress. What matters is not sending one document per round
trip.
