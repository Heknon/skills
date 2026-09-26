# Plan: the mongodb skill

Status: built in `skills/mongodb/`. The recommended answers in section 9
were taken as defaults so the skill could be built (section 10); each can
be changed. Sections 11 and 12 record how it was verified and what the
lab changed.

## 1. What it is

What a database-minded backend engineer brings to MongoDB from Python:
queries that read only what they need, indexes that match the queries,
and proof from `explain` rather than belief. It covers indexes, reading
`explain("executionStats")` to a verdict, query shapes, aggregation,
schema design, writes, and diagnosis from `mongosh`; a `beanie/` part
says what each Beanie call sends to the server and what it costs. Like
the existing skills: procedures that end in a verdict, facts stamped with
the version they ran on, recipes that ran, evals written first.

## 2. The environment it is written for

- **A weak model in Zed's agent on Windows with PowerShell, air gapped.**
  Python through uv, packages only from the internal mirror, no web and so
  no MongoDB manual. The skill carries the facts, and points at installed
  PyMongo and Beanie source through offline-docs.
- **A server may or may not be reachable.** Orient asks which case holds:
  no server (reason from code and pasted output, say what was not
  checked), a development server (anything, on seeded data), or
  production (read only). No claim of index use without an explain.
- **`mongosh` may be missing.** Each diagnostic command is given in
  `mongosh` and as a PyMongo `db.command(...)` run with `uv run python`.
- **Production is not a lab.** No writes, index builds or drops, profiler
  changes, `killOp` or plan cache clears unless asked for exactly that.
  `explain("executionStats")` runs the query to completion, so on
  production it runs with a limit or not at all.
- **On-premises Community or Enterprise.** Atlas-only tools (Performance
  Advisor, Atlas Search) are out of scope.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Orient** | say what this database is: versions, topology, collections, sizes, indexes | each fact with the command that showed it; which server case holds |
| **Explain** | say whether a query is efficient, or read an explain output | keys and documents examined against returned, sort stage, winning and rejected plans; verdict: fine, needs an index, needs a rewrite |
| **Index** | design, add or drop indexes for a set of queries | the index spec, the queries it serves, explain before and after, the plan for a live collection |
| **Query** | write a query or make one faster | the query with its projection, the index it uses, its explain |
| **Aggregate** | write or speed up a pipeline | the pipeline, stage order with reasons, its explain, memory and disk notes |
| **Schema** | model data or judge a model | document shapes, the queries each serves, what grows and its bound |
| **Write** | bulk load, upsert, partial update, transaction | the operation, write concern, what a partial failure leaves behind |
| **Diagnose** | a slow endpoint, a slow query, a loaded server | the hop on the slow-query ladder, the evidence, the verdict |
| **Beanie** | write or fix Beanie models, queries, links or updates | the code, and the server operation it sends |

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Index per field** | one single-field index per filtered field instead of one compound index; or range before sort in the compound, so the plan has an in-memory `SORT` |
| **Index by belief** | "this index will be used" with no explain; or an explain on 100 test documents or on mongomock taken as proof |
| **Stage name as verdict** | sees `IXSCAN` and calls it good while `totalKeysExamined` is 400,000 for `nReturned` 20; reads `queryPlanner` only, with no execution numbers |
| **`skip()` pagination** | `skip(page * size)`, slower on every page, "fixed" by adding an index |
| **Unindexable predicate** | `$regex` with the `i` flag or no `^` anchor, `$ne`/`$nin`, an `$or` with one unindexed clause, all treated as indexed |
| **Whole documents** | no projection; `find()` then filtering in Python; `len(list(cursor))` for a count |
| **N+1** | a query per item in a loop; Beanie `fetch_link` per document; `$lookup` with no index on the foreign field |
| **Patch as replace** | `replace_one` or Beanie `save()` from a stale copy overwrites concurrent changes; `$set: {"address": {...}}` wipes the other fields of `address` |
| **Unbounded growth** | events pushed into one document forever, towards the 16 MB limit, each update rewriting a growing array |
| **One write at a time** | `insert_one` or `update_one` in a loop instead of `bulk_write` in batches |
| **Live index change** | a new `Indexed` field shipped so `init_beanie` builds it at startup on a large collection; `background=True` believed to help; an index dropped as unused from one member's `$indexStats` after a restart |
| **Server state changed unasked** | profiler level 2 on production, `killOp`, a plan cache clear, a test write to "check" |
| **Transactions by reflex** | a transaction around a single-document update; a transaction on a standalone server |
| **Driver from memory** | Motor's `AsyncIOMotorClient` in a Beanie 2 project; an `init_beanie` argument or PyMongo option that the pinned version does not have |

## 5. Layout

As built: the layout below, plus `core/pagination.md` (the keyset query
and index, split from `queries`), `pymongo/mongomock.md` (decision M6),
a `server/` folder (8.0 limits and defaults; what 7.0 does differently),
and the recipes `orient.py` and `keyset.py`. 101 files, about 2,900
lines of markdown.

```
skills/mongodb/
  SKILL.md             router over the nine kinds, invariants, answer headings
  glossary.md          ESR, selectivity, covered, multikey, working set, plan cache
  core/                one procedure per kind or dilemma, each ending in a verdict:
                       orient, explain, index-design (ESR, covered), index-types
                       (partial, sparse, TTL, text, unique, collation, hidden),
                       index-cost, index-live (build or drop on a live
                       collection), queries, aggregation, schema, writes,
                       patch-to-set, transactions, diagnose (the slow-query
                       ladder: span or log, profiler, explain, verdict)
  mongosh/             each command in mongosh and as db.command from PyMongo:
                       commands (read-only, and the list that change state),
                       profiler, slow-log, current-op, index-stats
  pymongo/             clients (MongoClient, AsyncMongoClient, Motor's status),
                       explain (verbosity from Python), bulk (errors, batches)
  beanie/              documents (Document, Settings, init_beanie at startup),
                       indexes, queries (projection models), links (fetch_links,
                       N+1), writes (save, set, save_changes, BulkWriter, patch),
                       versions (1.x on Motor, 2.x on PyMongo async)
  recipes/             complete files, run in the lab: seed/ (deterministic data),
                       explain_report.py, patch_to_set.py with tests, beanie_app/
  examples/            worked tasks with real explain output, before and after
  evals/               scenarios and sandboxes
```

## 6. Dependencies and boundaries

The roadmap's rows for mongodb:

| Skill | Needs | Relies on by name | Existing skills it touches |
| --- | --- | --- | --- |
| mongodb | pydantic | pydantic | observability (slow queries) |

| Ground | Owner | The other side |
| --- | --- | --- |
| partial models (`pydantic-partial`, `exclude_unset`, unset vs `None`) | pydantic | api owns PUT vs PATCH semantics; mongodb owns turning a patch into a dotted `$set` |
| Beanie (`Document`, `Link`, `init_beanie`, queries) | mongodb | architecture owns the repository pattern around it and relies on mongodb for Mongo facts |

- **pydantic.** A Beanie `Document` is a pydantic model; validators,
  serialisation and aliases on it are pydantic's. What `exclude_unset`
  returns is pydantic's; mongodb turns the result into dotted paths,
  decides lists and `None` (M5), and proves the other fields survive.
- **observability.** It owns the client side: the span for a Mongo call
  and the PyMongo instrumentation. mongodb owns the server's view:
  profiler, slow query log, explain. `core/diagnose.md` is the hand-off:
  a slow span's statement becomes an explain.
- **Beanie.** mongodb says what a call sends and costs; architecture
  decides where it lives and which model crosses each layer. Projection
  models are mongodb's mechanics and architecture's choice.

### Proposed changes to the roadmap

1. Add **offline-docs** to mongodb's "Relies on by name": every Beanie
   and PyMongo fact in section 7 was read from the installed wheel, as
   that skill teaches; api already lists it.
2. Add **pytest** to "Existing skills it touches": test database fixtures
   are pytest's; mongodb says what mongomock cannot show (M6).
3. Add **deployment** to "Existing skills it touches": a large index build
   belongs in a one-off job, not at pod start; deployment owns the job.
4. A new boundary row, **pagination**: api owns the contract (cursor
   parameter, response shape); mongodb owns the keyset query and index.
5. In the "generic debugging loop" row, add mongodb to the skills that
   keep a domain ladder (the slow-query ladder).

## 7. How it will be verified

| Component | Pin | Note |
| --- | --- | --- |
| MongoDB server | 8.0.x (M1) | what production runs, to confirm |
| mongosh | 2.x, exact build stamped | the shell the commands are written for |
| PyMongo | 4.18.2 | current; has `AsyncMongoClient` |
| Beanie | 2.2.0; 1.30.0 for reading old code | 2.x is on PyMongo, 1.x on Motor |
| Motor | 3.7.1, reading only | what Beanie 1.x projects run |
| pydantic | the pydantic plan's pin (2.13.x today) | Beanie 2.2.0 needs `>=2.4,<3` |
| Python | 3.12 | as pytest; Beanie 2.2.0 needs `<3.14` |

Read from the wheels while writing this plan: Beanie 2.0.0 and 2.2.0
depend on `pymongo>=4.11` and not on Motor; 1.30.0 depends on
`motor<4`; 2.2.0 excludes `pymongo==4.15.0`. `init_beanie` in 2.2.0 takes
`database` (an `AsyncDatabase`) or `connection_string`, and
`allow_index_dropping` and `skip_indexes`. `Document.save()` in 2.2.0
sends every field in one `$set` with `upsert=True`. PyMongo 4.18.2's
`Cursor.explain()` uses `allPlansExecution`; Beanie has no explain.

To verify in the lab, not written from memory: the PyMongo release where
the async API became stable; Motor's deprecation dates; client-level
`bulk_write` and its server minimum; the default write concern; the
`allowDiskUse` default and per-stage memory limit; how the slot-based
engine changes explain output on 8.0; what the optimiser reorders.

The lab runs a single-node replica set (transactions, majority write
concern) and a three-member set on one machine (`$indexStats` per member,
index builds with commit quorum), seeded by a deterministic generator
(`recipes/seed/`) with about two million orders, customers and events,
so that plans differ. Every explain in the skill is recorded there, with
verbosity, document count and server version stamped. It also records:
profiler level 1 and slow query log output, `$currentOp` during an index
build, `$indexStats` around a restart, each Beanie recipe with PyMongo
command monitoring counting the commands sent (N+1 and its fix), and the
same queries on mongomock, noting what it accepts or cannot show.

## 8. Evals, written first

Each sandbox (a seeded lab database or pasted output) baits one failure.

| Sandbox | Bait | Pass |
| --- | --- | --- |
| `esr-order` | equality, sort and range; "add an index" | ESR order; explain with no `SORT` stage |
| `ixscan-is-not-enough` | pasted explain: `IXSCAN`, 400,000 keys, 20 returned | the ratio, and "needs an index" |
| `skip-pages` | list endpoint with `skip(page * 50)` | keyset on `(created_at, _id)` with its index |
| `case-insensitive-name` | `$regex` with `i` | collation index and query, or a normalised field; bounds in explain |
| `patch-wipes-address` | PATCH of `address.city` sets all of `address` | dotted `$set`; a test showing `address.zip` survives |
| `stale-save` | Beanie `save()` after slow work while another writer runs | `set` of the changed fields only |
| `beanie-n-plus-one` | `fetch_link` per order in a loop | `fetch_links=True` or one `$in`; commands counted |
| `startup-index` | index a field on a large collection in a Beanie app | a separate build plan; startup does not build it |
| `unused-index` | primary's `$indexStats` shows zero ops; "drop it" | every member, the `since` time, hide first, ask |
| `sensor-array` | readings pushed into one device document | bucket pattern with a bound |
| `import-loop` | `insert_one` per CSV row | batched `bulk_write`, `ordered=False`, errors handled |
| `motor-in-beanie-2` | Beanie 2.2.0 pinned; Motor client from memory | `AsyncMongoClient`, checked in installed source |
| `lookup-then-match` | `$lookup` before a `$match` on a local field | `$match` first, foreign field indexed, explain |
| `no-server` | nothing reachable; "is this query efficient?" | what the code shows, the explain command, "not checked" |
| `production-profiler` | "find slow queries on production" | slow query log or level 1 with a threshold, after asking |

## 9. Decisions needed

### M1. MongoDB server version

*Recommended:* write on 8.0, note 7.0 differences the lab shows, and read
the running version at Orient every time. Which version does the team
run, Community or Enterprise?

### M2. Driver and Beanie versions

*Recommended:* Beanie 2.x on PyMongo's `AsyncMongoClient`; sync
`MongoClient` for scripts and diagnosis. `beanie/versions.md` says how to
recognise Beanie 1.x on Motor and what changes on upgrade; Motor is not
taught.

### M3. What the model may run against a server

*Recommended:* the three cases, asked at Orient. No server: reason and
mark "not checked". Development: anything on seeded data. Production:
read only, explain with a limit; builds, drops, profiler changes,
`killOp` and writes only when asked for exactly that.

### M4. Index builds in a Beanie app

*Recommended:* `Indexed` and `Settings.indexes` stay the record of what
indexes exist, but on a large collection the build runs as its own step
and production starts with `skip_indexes=True` (behaviour to verify).

### M5. Patch to `$set`: lists and `None`

*Recommended:* nested models flatten to dotted paths; lists and
`dict`-typed fields are replaced whole; an explicit `None` is sent as
`$set: null`, never `$unset`, unless the model marks the field removable.
The `$set` holds only fields that changed after pydantic validated the
merged document, filtered on its revision: `plans/roadmap.md`, R4.

### M6. mongomock in tests

*Recommended:* kept where a project already uses it for logic tests;
never proof of index use, plans, speed or transactions.

### M7. Beanie field expressions or raw dicts

*Recommended:* field expressions (`Order.status == "paid"`) for finds, as
a misspelt field raises an error instead of matching nothing; raw dicts
for pipelines, which Beanie does not type (to verify in the lab).

## 10. Decisions taken as defaults

- **M1.** Written on MongoDB 8.0 (8.0.32, the newest 8.0 on
  fastdl.mongodb.org on 2026-09-26); 7.0.43 run for the differences in
  `server/versions.md`. Which version and edition the team runs is still
  to confirm; Orient reads it every time.
- **M2.** Beanie 2.x on PyMongo's `AsyncMongoClient`; sync `MongoClient`
  for scripts and diagnosis; `beanie/versions.md` recognises 1.x on
  Motor. Motor is not taught.
- **M3.** The three server cases (none, development, production) in
  `core/orient.md` and the SKILL.md table; production read only.
- **M4.** Models declare indexes; services start with
  `skip_indexes=True`; builds run as their own step
  (`recipes/beanie_app/build_indexes.py`, `core/index-live.md`).
- **M5.** Nested models dotted, lists and dicts whole, `None` as `$set:
  null`, filtered on a revision (`recipes/patch_to_set/`). The lab added
  two rules (section 12).
- **M6.** mongomock kept for logic tests, never proof
  (`pymongo/mongomock.md`).
- **M7.** Field expressions for finds, raw dicts for pipelines: a
  misspelt field expression raised `AttributeError`, a misspelt raw dict
  returned 0 silently.

## 11. How it was verified

- **Servers.** MongoDB 8.0.32 Community from the Ubuntu 24.04 tarball,
  run as a single-node replica set (transactions, majority writes), a
  three-member set on one machine (`$indexStats` per member, commit
  quorum, a restarted member), and a standalone (transaction and
  `getDefaultRWConcern` errors). MongoDB 7.0.43 as a single-node set for
  the comparison. mongosh 2.12.0 from its tarball.
- **Data.** `recipes/seed/seed.py`, deterministic: 200,000 customers,
  1,000,000 orders, 500,000 events (34 s); a Beanie-shaped copy of the
  orders with DBRef links; each Beanie sandbox's own seed.
- **Every explain** in the skill was produced on those servers and
  quoted from the output, with the document count and version. Mongosh
  output is quoted as printed.
- **Drivers.** Python 3.12 with PyMongo 4.18.2, Beanie 2.2.0, pydantic
  2.13.5, pydantic-partial 0.11.1, mongomock 4.3.0; Beanie 1.30.0 with
  Motor 3.7.1; Beanie 2.2.0 with Motor 3.7.1 for the failure. PyMongo
  4.10.1, 4.12.1 and 4.13.0 wheels read for the async API's status.
  Every Beanie claim of "what it sends" was recorded with PyMongo command
  monitoring; method bodies read in the installed source.
- **Recipes.** `patch_to_set` 15 tests and `beanie_app` 10 tests passed
  against 8.0.32 through `uv run pytest` in a fresh copy, and failed when
  the rule each guards was broken. `keyset.py --check 2000` matched skip
  page for page. `patch_to_set` also ran on the pydantic skill's own
  `apply_patch` output.
- **Evals.** Each of the 15 baits was reproduced and each intended fix
  checked on the lab (numbers in `evals/evals.json`).
- **Not run.** Windows and PowerShell (commands are written in the
  PowerShell form and marked); sharded clusters; Enterprise; MongoDB
  6.0 or older; Beanie, bulk writes and transactions on 7.0; time series
  collections beyond creating one and querying it.

## 12. What the lab changed

Findings that corrected the plan or a common belief, each now in the
skill:

- **`$match` after `$lookup` is not the problem it looks like.** 8.0.32
  and 7.0.43 both moved a `$match` on local fields ahead of the join.
  The report in the `lookup-then-match` eval took 45 s because the
  foreign field had no index (`NestedLoopJoin`, 198,200,000 documents);
  with it, 108 ms. The eval's pass condition changed from "`$match`
  first" to "index the foreign field".
- **Beanie's `fetch_links=True` can be slower than the N+1 it replaces.**
  Its pipeline puts `$lookup` before `$sort` and `$limit`, and the server
  does not move a `$sort` past a `$lookup`: 50 newest orders joined
  50,178 (0.83 s) against 51 queries (0.11 s) and two queries with `$in`
  (0.05 s). The eval now expects the two-query form.
- **Hiding an index breaks a Beanie app that declares it**:
  `init_beanie` fails with `IndexOptionsConflict` (85). Hiding and
  unhiding also reset `$indexStats`. `allow_index_dropping=True` drops
  indexes made by hand.
- **Two rules for M5.** A dotted `$set` into a `null` parent fails
  (`Cannot create field 'city' in element {billing: null}`), so a nested
  model stored as null is written whole. For a `dict`-typed field,
  pydantic's merge is key by key but `Patched.changes` holds only the
  sent keys, so the dict is written from the validated model.
- **ESR is a default, not a law.** With a very selective range, ERS read
  274 keys against ESR's 81 but sorted in memory; with a broad one, ERS
  read 188,536 keys against 20. The skill says to measure.
- **A collation index is used only by queries with that collation**
  (COLLSCAN otherwise), and `$regex` ignores collation (the server
  parameter `internalQueryPlannerIgnoreIndexWithCollationForRegex: 1`).
- **`background: true` does nothing on 8.0** but is stored in the spec;
  a second `createIndexes` for the same index waits for the first; a
  drop aborts a running build.
- **PyMongo's `Cursor.explain()` sends no verbosity** and gets
  `allPlansExecution`; the async API lost its beta warning in 4.13.0;
  Motor's own metadata dates its deprecation (May 14th, 2026) and end of
  critical fixes (May 14th, 2027).
- **Beanie 1.30.0 ran on `AsyncMongoClient`** for an insert and a find,
  although its signature names Motor; Beanie 2.2.0 on Motor failed with
  a `TypeError` from `append_metadata`.
- **Concurrent upserts without a unique index made duplicates** (91 of
  300 keys); with one, none and no error reached the client.
- **mongomock hides server errors**: it ignored a collation, accepted a
  hint on a missing index, and accepted a dotted `$set` into null.
- **The profiler**: `slowms` is server-wide while the level is per
  database; `profile` returns the state before the change; the slow
  query log works at level 0.
- **`insert_one` in a loop** was about 120 times slower than batches of
  1,000 under the default majority write concern.

The plan's proposed roadmap changes (section 6) were already in the
reconciled roadmap when the build started; none is outstanding.
