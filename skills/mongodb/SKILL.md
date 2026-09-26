---
name: mongodb
description: Make MongoDB work efficiently from Python, with proof from the server. Say what a deployment is (version, topology, collections, sizes, indexes), read explain("executionStats") to a verdict, design compound indexes (ESR order, covered queries, partial, sparse, TTL, text, unique, collation, hidden), build or drop an index on a live collection, write queries with projections, keyset pagination instead of skip, case-insensitive search, aggregation pipelines and $lookup, schema design and unbounded arrays, bulk loads and upserts, partial updates as a dotted $set guarded by a revision (the PATCH hand-off from pydantic), transactions, and diagnosing a slow endpoint, query or server with the profiler, the slow query log and $currentOp. Beanie models, init_beanie, Indexed, Link and fetch_links, save, set and revisions, projection models, and what each call sends to the server; PyMongo's MongoClient and AsyncMongoClient; Motor and Beanie 1.x in old code; mongomock's limits. Verified on MongoDB 8.0.32 (and 7.0.43 where they differ), mongosh 2.12.0, PyMongo 4.18.2, Beanie 2.2.0 and 1.30.0, Motor 3.7.1.
---

# MongoDB

This skill knows how a MongoDB server plans, runs and writes, and what
PyMongo and Beanie send to it. Every command, option, plan stage, number
and error message in it was run on MongoDB 8.0.32 with PyMongo 4.18.2
and Beanie 2.2.0, on seeded collections of up to a million documents.
Nothing is written from memory: find the fact here, in the server's own
output, or in the installed driver's source (offline-docs skill).

Read this file, then load only what the task needs.

## Read the versions first, and which server you have

```
uv pip show pymongo beanie motor        # "not found" for one not installed
uv run --no-sync python <skill>/recipes/orient.py --uri "$env:MONGODB_URI" --db <name>
```

`recipes/orient.py` prints the server version, topology, default write
concern, profiler level, and every collection with its sizes and indexes
(read only). Then decide which case holds (`core/orient.md`):

| Case | You may |
| --- | --- |
| **No server** | reason from code and pasted output; mark every plan claim `not checked`; give the command that would check it |
| **Development** (seeded or copied data) | anything: explain, create and drop indexes, write test data |
| **Production** | read only. Explain with a `limit` or not at all. No writes, index builds or drops, profiler changes, `killOp` or plan cache clears unless asked for exactly that |

If nothing says which, ask. A server whose name or data looks like
production is production.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Orient** | say what this database is: versions, topology, collections, sizes, indexes | `core/orient.md` |
| **Explain** | say whether a query is efficient, or read an explain output | `core/explain.md`, `pymongo/explain.md` |
| **Index** | design, add or drop indexes for a set of queries | `core/index-design.md`, `core/index-types.md`, `core/index-cost.md`, `core/index-live.md` |
| **Query** | write a query or make one faster; page through results; search text | `core/queries.md`, `core/pagination.md` |
| **Aggregate** | write or speed up a pipeline, a `$lookup`, a report | `core/aggregation.md` |
| **Schema** | model data or judge a model; arrays that grow | `core/schema.md` |
| **Write** | bulk load, upsert, partial update, PATCH, transaction | `core/writes.md`, `core/patch-to-set.md`, `core/transactions.md`, `pymongo/bulk.md` |
| **Diagnose** | a slow endpoint, a slow query, a loaded server | `core/diagnose.md`, then the `mongosh/` file it names |
| **Beanie** | write or fix Beanie models, queries, links, updates or startup | `beanie/` file for the part, and `beanie/versions.md` first |

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above; each ends in a verdict |
| `mongosh/` | each diagnostic command in mongosh and as PyMongo: the read-only list and the ones that change state, profiler, slow query log, `$currentOp`, `$indexStats` |
| `pymongo/` | clients (sync, async, Motor's status), explain from Python, bulk writes and their errors, mongomock's limits |
| `beanie/` | documents and `init_beanie`, indexes, queries and projections, links and N+1, writes and revisions, versions 1.x and 2.x |
| `server/` | limits and defaults of 8.0, and what 7.0 does differently |
| `recipes/` | complete files that ran: `orient.py`, `explain_report.py`, `keyset.py`, `seed/` (deterministic data), `patch_to_set/` with tests, `beanie_app/` with tests |
| `examples/` | four finished tasks: an index for a list endpoint (`esr-index.md`), a 45-second report (`lookup-report.md`), a PATCH that wiped an address (`patch-address.md`), a Beanie N+1 (`beanie-n-plus-one.md`) |

`glossary.md` fixes the words. Other skills own neighbouring ground:
pydantic (partial models, validating a patch), api (a PATCH's meaning,
status codes, the pagination contract), architecture (the repository
around Beanie, which layer owns a transaction), observability (the span
for a Mongo call), deployment (running an index build as a job), pytest
(fixtures), offline-docs (reading installed PyMongo and Beanie).

## Invariants

1. **No claim of index use or speed without `explain("executionStats")`**
   from a server holding realistic data. Not from `queryPlanner` alone,
   not on a hundred test documents, never on mongomock.
2. **The numbers decide, not the stage name.** Compare
   `totalKeysExamined` and `totalDocsExamined` with `nReturned`, and look
   for a `SORT` stage. `IXSCAN` with 400,000 keys for 21 documents is not
   efficient (`core/explain.md`).
3. **Production is read only** unless the person asked for that exact
   change. Explain there with a `limit`: executionStats runs the query.
4. **One compound index per query shape, fields in ESR order**:
   equality, then sort, then range (`core/index-design.md`).
5. **A partial update is a dotted `$set` of the changed paths**, filtered
   on the revision it was read with. Never `replace_one` or Beanie
   `save()` of a copy that other writers may have changed.
6. **Batches, not loops.** No query or write per item: `$in`, one
   `$lookup`, `insert_many` or `bulk_write` in batches.
7. **An index build on a large collection is its own step**, never an
   application's startup; a drop is preceded by hiding the index and
   reading `$indexStats` on every member.
8. **Driver facts from the installed source.** Beanie 2 runs on PyMongo's
   `AsyncMongoClient`, not Motor; check `uv pip show` and the signature
   before writing startup code.

## What you say when you finish

End with these headings, each with `none` when empty. If another skill
is loaded, its headings come first and these after.

```
## Result
<the query, index, pipeline or code, with paths; the verdict>

## Checked
<server version and case (none, development, production); each explain or
command run, with nReturned, keys and documents examined, time, stages;
before and after for a change>

## Not checked
<what needs a server, another member, production data or a person's go-ahead>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
