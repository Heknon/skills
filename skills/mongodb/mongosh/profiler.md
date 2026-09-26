# The profiler

MongoDB 8.0.32, *lab*. The profiler writes one document per recorded
operation into `system.profile` of the database it is on. It changes
server state: on production, only after the person agreed to the exact
command, the database, the threshold and when it goes off again.

## Levels

| Level | Records | Use |
| --- | --- | --- |
| 0 | nothing into `system.profile`; operations over `slowms` still go to the log | the default; read the log first (`mongosh/slow-log.md`) |
| 1 | operations slower than `slowms`, or matching `filter` | a bounded look at one database |
| 2 | every operation | development only |

`slowms` is server-wide; the level is per database. *lab*: after
`db.command("profile", 0, slowms=250)` on `shop`, `profile -1` on `lab`
showed `slowms 250, level 0`; after `profile 1` on `shop`, `shop` was at
level 1 and `lab` at 0.

## Read the state (read only)

```
db.getProfilingStatus()              # { was: 0, slowms: 100, sampleRate: 1 }
```

PyMongo: `db.command("profile", -1)`.

## Turn it on, and off again

```
db.setProfilingLevel(1, {slowms: 200})
db.setProfilingLevel(1, {filter: {millis: {$gte: 150}}})
db.setProfilingLevel(0)
```

PyMongo: `db.command("profile", 1, slowms=200)`, `db.command("profile",
1, filter={"millis": {"$gte": 150}})`, `db.command("profile", 0)`. Each
returns the state **before** the change (*lab*: `{'was': 0, 'slowms':
100}`). A filter stays set until removed: `db.command("profile", 0,
filter="unset")` (*lab*: afterwards `profile -1` showed no `filter`).

## Read what it recorded

```
db.system.profile.find({ns: "shop.orders"}).sort({ts: -1}).limit(5)
```

*lab*, a query tagged with `comment("lab-slow-2")` at level 1, slowms
50 (abridged):

```
op: 'query', ns: 'shop.orders',
command: { find: 'orders', filter: { 'address.city': 'Lyon', total_cents: { '$gte': 390000 } }, comment: 'lab-slow-2', ... },
keysExamined: 0, docsExamined: 1000000, nreturned: 0,
planSummary: 'COLLSCAN', millis: 342, queryFramework: 'classic',
execStats: { stage: 'COLLSCAN', ... docsExamined: 1000000 },
ts: ISODate('2026-09-26T05:52:54.303Z'), appName: 'mongosh 2.12.0'
```

The comment is under `command.comment`, not at the top level: filter
with `{"command.comment": "lab-slow-2"}`. The fields to judge are the
same as explain's: `planSummary`, `keysExamined`, `docsExamined` against
`nreturned`, and `millis` (`core/explain.md`).

## What to propose on production

"Level 1 on database `<db>` with `slowms: <n>` (or a `filter` on the
namespace), for <30 minutes> during the slow period, then `profile 0`;
I will read `system.profile` and turn it off." Never level 2.
