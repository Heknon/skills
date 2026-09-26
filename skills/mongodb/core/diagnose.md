# Diagnose: the slow-query ladder

**Verdict you produce:** the hop where the time goes, the evidence, and
the fix.

```
symptom:   <endpoint or job, how slow, since when>
hop:       <n. name>
evidence:  <the span, log line, profile entry or explain, quoted>
cause:     <one sentence>
fix:       <index | rewrite | batch | schema>, checked by <explain before and after>
asked:     <any server change that needs a person's go-ahead>
```

## The ladder

Go down in order; the first hop whose evidence is wrong is where you
work. On production every hop is read only until a person approves a
change (`core/orient.md`).

| # | Hop | Evidence | Healthy looks like |
| --- | --- | --- | --- |
| 1 | the request's time is in Mongo calls | the trace: spans with `db.system=mongodb` and their durations (observability skill owns the spans) | Mongo spans are a small part of the request |
| 2 | how many calls | span count per request, or PyMongo command monitoring (`pymongo/clients.md`) | a fixed number, not one per item (N+1, `beanie/links.md`) |
| 3 | which statement is slow | the slow query log (`mongosh/slow-log.md`): `planSummary`, `keysExamined`, `docsExamined`, `nreturned`, `durationMillis` | examined close to returned |
| 4 | what the server did | `explain("executionStats")` of that statement, with a limit on production (`core/explain.md`) | no COLLSCAN or SORT on a large collection; keys near returned |
| 5 | is it waiting, not working | `$currentOp` (`mongosh/current-op.md`): `waitingForLock`, long `secs_running`, an index build | nothing waiting |
| 6 | is the server short of memory | `serverStatus().wiredTiger.cache`: bytes in cache against maximum; indexes' total size (`core/index-cost.md`) | the used indexes fit |

The observability skill owns the client side (the span, its attributes,
PyMongo instrumentation). A slow span's statement becomes an explain at
hop 4: take the command from the span or the slow log, put its filter,
sort and limit into `recipes/explain_report.py`.

## Hop 3 without changing anything

The server already logs every operation slower than `slowms` (100 ms by
default), even at profiler level 0. *lab, 8.0.32*: at level 0 a 362 ms
COLLSCAN was logged as `Slow query` and nothing went to `system.profile`.
A log line (this one from a 342 ms run) reads

```
"msg":"Slow query","attr":{"type":"command","ns":"shop.orders", ...
"planSummary":"COLLSCAN","keysExamined":0,"docsExamined":1000000,
"nreturned":0,"queryFramework":"classic", ... "durationMillis":342,
"workingMillis":342}
```

Read it with `db.adminCommand({getLog: "global"})` (recent lines held in
memory; *lab*: 1,023 of 2,560 written) or from the mongod log file.
Add `.comment("<tag>")` to a query (PyMongo `comment=`) to find it in
the log and in `$currentOp`.

## When the log is not enough

The profiler (`mongosh/profiler.md`) records each slow operation in
`system.profile` of one database, with its execution stats: one write
per recorded operation. Turning it on changes server state; on
production, ask first and
propose level 1 with a threshold, on one database, for a bounded time,
then level 0. Never level 2 on production.

## Verdicts

| Evidence | Cause | Fix |
| --- | --- | --- |
| one call per item | N+1 | `$in`, one `$lookup`, batch (`beanie/links.md`) |
| COLLSCAN, or keys far above returned | no matching index | `core/index-design.md` |
| SORT with `usedDisk` | sort not served by an index | the sort field in the index |
| SKIP with a large `skipAmount` | skip pagination | `core/pagination.md` |
| `$lookup` NestedLoopJoin | no index on the foreign field | `core/aggregation.md` |
| `waitingForLock`, an index build in `$currentOp` | a build or a long transaction | wait, or schedule builds (`core/index-live.md`) |
| fast in explain, slow in the application | too many round trips, large documents, no projection | `core/queries.md` |

## Never

- Never set the profiler to level 2, kill an operation, or clear the plan
  cache on production without a person's go-ahead for that action.
- Never report "the database is slow" without the statement and its
  numbers.
