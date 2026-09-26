# Orient

**Verdict you produce:** what the deployment is, each fact with the
command that showed it, and which server case holds.

```
server case:  <none | development | production>, because <what the person said or the URI shows>
version:      <8.0.32>, FCV <8.0>, <Community | Enterprise>    (buildInfo, getParameter)
topology:     <standalone | replica set rs0, n members | sharded>  (hello)
default w:    <majority>                                         (getDefaultRWConcern)
collections:  <name: count, data MB, index MB, indexes>          ($collStats, listIndexes)
drivers:      pymongo <4.18.2>, beanie <2.2.0 | not installed>, motor <... | not installed>
```

## 1. Which server case

Ask, or read it from the task. Then keep to its rules for the whole task.

| Case | Signs | Rules |
| --- | --- | --- |
| no server | no URI, the connection is refused, the person pasted output | reason from code and pasted output; every plan claim is `not checked`; give the exact command that would check it |
| development | a local or test URI; data seeded or copied | anything: explain, index builds and drops, test writes |
| production | a production host name, a read-only account, the person says so | read only; explain with a `limit`; nothing that changes state unless asked for exactly that (`mongosh/commands.md` lists what changes state) |

When the case is unclear, it is production.

## 2. Versions and topology in one run

`recipes/orient.py` sends only read-only commands and scans no
collection (counts are metadata estimates):

```
uv run --no-sync python <skill>/recipes/orient.py --uri "$env:MONGODB_URI" --db shop
```

*lab, 8.0.32, single-node replica set, seeded shop database (abridged):*

```
version:            8.0.32   (buildInfo)
FCV:                8.0   (getParameter featureCompatibilityVersion)
modules:            none (Community)   (buildInfo; enterprise = Enterprise)
topology:           replica set rs0, members ['127.0.0.1:27017']   (hello)
connected to:       127.0.0.1:27017 primary=True
default w:          {'w': 'majority', 'wtimeout': 0} source=implicit   (getDefaultRWConcern)
profiler on shop:   level 0, slowms 100   (profile -1, read only)

orders: ~1,000,000 docs, avg 356 B, data 340.0 MB, indexes 157.0 MB   ($collStats storageStats)
  _id_: {'_id': 1}  61.7 MB
  customer_id_1: {'customer_id': 1}  8.6 MB
```

On a standalone server the same script prints `topology: standalone (no
transactions)` and `default w: not readable: Location51300`
(`getDefaultRWConcern` is not supported on standalone nodes).

The same facts in mongosh, one at a time (*lab*, mongosh 2.12.0):

| Fact | mongosh | PyMongo (`c = MongoClient(uri)`) |
| --- | --- | --- |
| version | `db.version()` -> `8.0.32` | `c.admin.command("buildInfo")["version"]` |
| FCV | `db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1})` | `c.admin.command("getParameter", 1, featureCompatibilityVersion=1)` |
| topology | `db.hello()`: `setName`, `hosts`, `isWritablePrimary` | `c.admin.command("hello")` |
| default write concern | `db.adminCommand({getDefaultRWConcern: 1})` | `c.admin.command("getDefaultRWConcern")` |
| collections | `db.getCollectionNames()` | `db.list_collection_names()` |
| count (metadata) | `db.orders.estimatedDocumentCount()` | `db.orders.estimated_document_count()` |
| sizes | `db.orders.aggregate([{$collStats: {storageStats: {}}}])` | same pipeline with `aggregate` |
| indexes | `db.orders.getIndexes()` | `db.orders.list_indexes()` or `index_information()` |

`countDocuments({})` scans; on production use the estimate.

## 3. What the numbers tell you

- **Topology decides what is possible.** Transactions need a replica set
  or sharded cluster; on a standalone the first transactional write fails
  with `Transaction numbers are only allowed on a replica set member or
  mongos` (`core/transactions.md`). `$indexStats` is per member
  (`mongosh/index-stats.md`).
- **Index size against data size.** Indexes of 157 MB on 340 MB of data
  are normal; indexes larger than the data suggest indexes nobody uses
  (`core/index-cost.md`).
- **Hidden indexes** show `{'hidden': True}` in the index line.
- **The profiler level** shows whether someone left it on: level 2 on
  production is a finding in itself (`mongosh/profiler.md`).

## 4. The drivers

```
uv pip show pymongo beanie motor
```

Then `beanie/versions.md`: Beanie 2.x runs on PyMongo, 1.x on Motor.

## Never

- Never run `countDocuments({})`, a `find()` without a limit, or an
  explain without a limit on a large production collection "to see".
- Never write a test document to production to check that writes work.
