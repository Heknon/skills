# Index use counters: `$indexStats`

Read only. MongoDB 8.0.32, *lab* on a three-member replica set.

```
db.orders.aggregate([{$indexStats: {}}, {$project: {name: 1, host: 1, accesses: 1}}])
```

PyMongo: `list(db.orders.aggregate([{"$indexStats": {}}, {"$project":
{"name": 1, "host": 1, "accesses": 1}}]))`.

## What the counters are

- **Per member.** Each member counts the operations that used the index
  **on that member**. The answer comes from the member you are connected
  to (`host`). *lab*: queries on `country` sent to secondaries; the
  primary showed `country_1` with `ops: Long('0')`, the secondaries 3
  and 4.
- **Since a time.** `accesses.since` is when counting started. It resets
  when the member restarts and when the index is hidden or unhidden.
  *lab*: after a restart of one secondary its `country_1` showed `ops:
  Long('0'), since: ISODate('2026-09-26T05:51:12.109Z')`, the restart
  time; after `collMod` hide and unhide on the primary, 2 ops became 0
  and `since` moved to the `collMod` time.
- **Counts uses, not cost.** An index used once a month by the month-end
  report shows 0 for four weeks.

## Read every member

Connect to each member directly and read the counters with a read
preference that allows a secondary:

```
mongosh --port 27022 shop --eval 'db.getMongo().setReadPref("secondaryPreferred"); db.orders.aggregate([{$indexStats: {}}]).toArray()'
```

PyMongo: `MongoClient("mongodb://host:27022/?directConnection=true",
readPreference="secondaryPreferred")`.

## Before believing a zero

| Check | Why |
| --- | --- |
| every member's counter | reads may go to secondaries (reports, analytics, `readPreference` in URIs) |
| `since` on each | a restart or a hide/unhide resets it; compare with the other indexes' `since` |
| a full business cycle since `since` | monthly and quarterly jobs |
| the code of every service on the database | a query that runs rarely |
| Beanie models that declare it | hiding it breaks `init_beanie` (`core/index-live.md`) |

Then hide, watch, and only then propose the drop (`core/index-live.md`).
