# Recipes

Complete files that ran against MongoDB 8.0.32 with PyMongo 4.18.2
(and Beanie 2.2.0 where named), Python 3.12. Copy one whole and change
only what its top comment says.

| Recipe | What it is | Changes state? |
| --- | --- | --- |
| `orient.py` | versions, topology, write concern, profiler level, collections, sizes and indexes (`core/orient.md`) | no |
| `explain_report.py` | runs or reads an explain and prints plan, numbers and verdict (`core/explain.md`) | no (the explain runs the query) |
| `keyset.py` | keyset pagination on `(created_at, _id)`, with a check against skip (`core/pagination.md`) | no |
| `seed/seed.py` | deterministic shop data: 200,000 customers, 1,000,000 orders, 500,000 events | **drops and rewrites** its collections: development only |
| `patch_to_set/` | a validated PATCH as a dotted `$set` with a revision, and tests (`core/patch-to-set.md`) | its server tests use their own database |
| `beanie_app/` | Beanie 2.2.0 models, startup without index builds, queries without N+1, patches with revisions, an index job, and tests that count commands | its tests use their own database |

The single-file recipes carry inline script metadata (`# /// script`),
so `uv run <file> --help` works with nothing else installed when the
mirror has `pymongo`. Inside a project that already has PyMongo, run
them with `uv run --no-sync python <file>`.

## Run the tests (PowerShell or POSIX)

```
cd recipes/patch_to_set
uv run pytest                              # 9 passed, 6 skipped without a server
$env:MONGODB_URI = "mongodb://localhost:27017/?replicaSet=rs0"
uv run pytest                              # 15 passed

cd ../beanie_app
uv run pytest                              # 10 passed with MONGODB_URI set
```

*lab*: those counts on Linux; the PowerShell lines were not run on
Windows. The server tests need a development server, never production:
they drop the databases `patch_to_set_test` and `beanie_app_test`.

## A development server

A single-node replica set (transactions and majority writes work):

```
mongod --replSet rs0 --dbpath <dir> --port 27017 --bind_ip 127.0.0.1
mongosh --eval 'rs.initiate({_id: "rs0", members: [{_id: 0, host: "127.0.0.1:27017"}]})'
uv run seed/seed.py --uri "mongodb://127.0.0.1:27017/?replicaSet=rs0"
```

*lab*: seeding the defaults took 34 s. On Windows, `mongod.exe` takes the
same options (not run on Windows).
