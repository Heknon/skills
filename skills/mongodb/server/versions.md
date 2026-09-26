# MongoDB 8.0 and 7.0

The skill is written on 8.0.32 (decision M1). The same seeded data and
queries were run on 7.0.43 for the facts below. Read the server's
version at Orient every time (`core/orient.md`).

| Topic | 8.0.32 | 7.0.43 |
| --- | --- | --- |
| ESR query `{country, status, total_cents >= 100000}` sort `created_at` | `LIMIT <- FETCH <- IXSCAN`, 81 keys, 20 docs | the same plan and numbers |
| `find` explain | `explainVersion: '1'`; `queryPlanner` has `planCacheShapeHash`, `prunedSimilarIndexes`; top level has `queryShapeHash` | `explainVersion: '1'`; no `planCacheShapeHash` or `prunedSimilarIndexes` |
| `$match` + `$group` explain | `explainVersion: '2'` (SBE) | `explainVersion: '1'` |
| `$lookup` into an unindexed foreign field | pushed into the query: `EQ_LOOKUP`, `strategy: 'NestedLoopJoin'`; 198 customers: 45 s | a separate `$lookup` stage with `collectionScans: 198`, `totalDocsExamined: 198000000`; 62.6 s |
| `$match` on local fields after `$lookup` | moved before the join | moved before the join |
| profiler and slow log entries | have `queryShapeHash`, `planCacheShapeHash` | not checked |

`recipes/explain_report.py` reads both shapes: it follows `queryPlan`
under `winningPlan` when present and reads `collectionScans` on a
`$lookup` stage.

Not run on 7.0: Beanie, bulk writes, index builds, transactions. No 6.0
or older server was run.
