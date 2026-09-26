# Commands: read only, and the ones that change state

Each command as typed in mongosh 2.12.0 and as PyMongo 4.18.2 sends it,
run on MongoDB 8.0.32. When `mongosh` is not installed, run the PyMongo
form in a file with `uv run --no-sync python file.py`. `c =
MongoClient(uri)`, `db = c["shop"]`.

## Read only: safe on production

| Question | mongosh | PyMongo |
| --- | --- | --- |
| version | `db.version()` | `c.admin.command("buildInfo")["version"]` |
| topology | `db.hello()` | `c.admin.command("hello")` |
| default write concern | `db.adminCommand({getDefaultRWConcern: 1})` | `c.admin.command("getDefaultRWConcern")` |
| a server parameter | `db.adminCommand({getParameter: 1, allowDiskUseByDefault: 1})` | `c.admin.command("getParameter", 1, allowDiskUseByDefault=1)` |
| collection sizes | `db.orders.aggregate([{$collStats: {storageStats: {}}}])` | `db.orders.aggregate([{"$collStats": {"storageStats": {}}}])` |
| indexes | `db.orders.getIndexes()` | `db.orders.index_information()` |
| index use counters | `db.orders.aggregate([{$indexStats: {}}])` | same pipeline (`mongosh/index-stats.md`) |
| explain | `db.orders.find(q).limit(20).explain("executionStats")` | `db.command("explain", {"find": "orders", "filter": q, "limit": 20}, verbosity="executionStats")` |
| profiler level | `db.getProfilingStatus()` | `db.command("profile", -1)` |
| recent log lines | `db.adminCommand({getLog: "global"})` | `c.admin.command("getLog", "global")` |
| running operations | `db.getSiblingDB("admin").aggregate([{$currentOp: {}}, {$match: ...}])` | `c.admin.aggregate([{"$currentOp": {}}, {"$match": ...}])` |
| cached plans | `db.orders.aggregate([{$planCacheStats: {}}])` | same pipeline |
| cache and op counters | `db.serverStatus().wiredTiger.cache`, `.opcounters` | `c.admin.command("serverStatus")` |

`explain("executionStats")` reads, but runs the query to completion: on
production give it a limit.

`getLog` takes a log name: *lab*, `c.admin.command("getLog", "*")`
returned `['global', 'startupWarnings']`.

`currentOp` as a command takes its filter at the top level: `c.admin.
command({"currentOp": 1, "active": True})`. `c.admin.command("currentOp",
{...})` puts the filter in the wrong place and returns every operation
(*lab*). Prefer the `$currentOp` pipeline.

## Change state: only when asked for exactly that

| Action | mongosh | PyMongo | What it changes |
| --- | --- | --- | --- |
| profiler on | `db.setProfilingLevel(1, {slowms: 200})` | `db.command("profile", 1, slowms=200)` | this database's level; `slowms` for the whole server |
| profiler off | `db.setProfilingLevel(0)` | `db.command("profile", 0)` | |
| kill an operation | `db.killOp(<opid>)` | `c.admin.command("killOp", op=<opid>)` | the operation fails: `operation was interrupted` |
| clear cached plans | `db.orders.getPlanCache().clear()` | `db.command("planCacheClear", "orders")` | every query shape replans |
| build an index | `db.orders.createIndex(...)` | `db.orders.create_index(...)`, or `createIndexes` with `commitQuorum` | `core/index-live.md` |
| hide or unhide | `db.runCommand({collMod: "orders", index: {name: "x", hidden: true}})` | `db.command("collMod", "orders", index={"name": "x", "hidden": True})` | planner ignores it; resets `$indexStats` |
| drop an index | `db.orders.dropIndex("x")` | `db.orders.drop_index("x")` | |
| set a parameter | `db.adminCommand({setParameter: 1, ...})` | `c.admin.command("setParameter", 1, ...)` | server-wide |
| any write | `insertOne`, `updateOne`, ... | `insert_one`, `update_one`, ... | data |

*lab*: `db.command("profile", 1, slowms=200)` returned the previous
state `{'was': 0, 'slowms': 100}`; the new state is read with `profile
-1`. `killOp` returned `{'info': 'attempting to kill op', 'ok': 1.0}`.

Before any row of this table on production: say what it changes, how to
undo it, and get the person's go-ahead for that action.
