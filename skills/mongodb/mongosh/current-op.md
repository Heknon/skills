# Running operations: `$currentOp`

Read only. Shows what the server is doing now: long queries, index
builds, operations waiting for a lock. MongoDB 8.0.32, *lab*.

## Ask

```
db.getSiblingDB("admin").aggregate([
  {$currentOp: {}},
  {$match: {active: true, secs_running: {$gte: 2}}},
  {$project: {opid: 1, secs_running: 1, op: 1, ns: 1, planSummary: 1,
              "command.comment": 1, client: 1, waitingForLock: 1, msg: 1, progress: 1}}
])
```

PyMongo: `list(c.admin.aggregate([{"$currentOp": {}}, {"$match":
{...}}, {"$project": {...}}]))`. Tag your own queries with a comment
(`.comment("report-q3")`, PyMongo `comment=`) and match on
`"command.comment"`.

## A slow query, seen

*lab*, a query tagged `lab-long`, 1.5 s in:

```
{'client': '127.0.0.1:42880', 'opid': 681985, 'secs_running': 1, 'microsecs_running': 1497114,
 'op': 'query', 'ns': 'shop.orders', 'planSummary': 'COLLSCAN'}
```

## An index build, seen

*lab*, 1.2 s into a build on 1,000,000 orders:

```
{ desc: 'IndexBuildsCoordinatorMongod-5', active: true, opid: 344066, secs_running: Long('1'),
  op: 'command', command: { createIndexes: 'orders', indexes: [ { name: 'items.sku_1_created_at_1_total_cents_1' } ] },
  msg: 'Index Build: scanning collection Index Build: scanning collection: 640363/1000000 64%',
  progress: { done: 640363, total: 1000000 }, waitingForLock: false }
```

There were two entries: the client's `createIndexes` (`desc: 'conn322'`)
waiting for the build, and the build itself
(`IndexBuildsCoordinatorMongod-5`) with the progress.

## Killing an operation (changes state)

`db.killOp(<opid>)`, PyMongo `c.admin.command("killOp", op=<opid>)`.
*lab*: it returned `{'info': 'attempting to kill op', 'ok': 1.0}` and the
query's client got `OperationFailure: ... operation was interrupted`.
Only when the person asked for that operation to be killed; the
application sees an error. To stop an index build, drop the index
instead (`core/index-live.md`).
