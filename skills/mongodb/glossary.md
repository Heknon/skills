# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| query shape | A filter, sort and projection with the values taken out; queries of one shape share a plan cache entry (`planCacheShapeHash`). |
| plan | The tree of stages the server runs for a query, such as `LIMIT <- FETCH <- IXSCAN`; read root first. |
| winning plan | The plan the planner chose, in `queryPlanner.winningPlan` (explain version 2 nests it under `queryPlan`). |
| rejected plan | A candidate plan the planner tried and discarded, in `rejectedPlans`. |
| explain verbosity | How much explain runs: `queryPlanner` (plans, no execution), `executionStats` (runs the winning plan to completion), `allPlansExecution` (also the trial runs). |
| COLLSCAN | A stage that reads every document of the collection. |
| IXSCAN | A stage that walks a range of one index's keys, the **index bounds**. |
| FETCH | A stage that loads the documents behind index keys; a `filter` on it drops documents after loading them. |
| blocking sort | A `SORT` stage: the server holds results in memory (100 MB per stage by default) and sorts them because no index gives the order. |
| index bounds | The key ranges an IXSCAN reads; `[MinKey, MaxKey]` on a field means it constrains nothing. |
| keys examined | `totalKeysExamined`: index entries read; compare with `nReturned`. |
| docs examined | `totalDocsExamined`: documents loaded; compare with `nReturned`. |
| selectivity | The share of documents a predicate matches; a selective predicate matches few. |
| compound index | One index on several fields in a fixed order; it serves queries on any prefix of that order. |
| ESR | The field order for a compound index: **E**quality fields first, then the **S**ort fields, then the **R**ange fields. |
| covered query | A query answered from the index alone: no FETCH, `totalDocsExamined` 0; the projection must exclude `_id` unless `_id` is in the index. |
| multikey index | An index on a field that holds an array in some document: one key per element. |
| partial index | An index holding only documents that match its `partialFilterExpression`; used only when the query implies that filter. |
| sparse index | An index skipping documents that lack the field. |
| TTL index | A single-field date index with `expireAfterSeconds`; a background task deletes expired documents about once a minute. |
| collation | Rules for comparing strings (locale, strength); strength 2 ignores case. An index with a collation serves only queries with the same collation. |
| hidden index | An index the planner ignores but the server keeps up to date; unhiding is instant. |
| index build | Creating an index on existing data; on a replica set every voting member builds it and the **commit quorum** decides when it commits. |
| working set | The documents and index pages a workload touches; performance falls when it no longer fits the WiredTiger cache. |
| plan cache | The server's memory of the winning plan per query shape; emptied for a collection when an index on it is created or dropped, or by `planCacheClear`. |
| slot-based engine (SBE) | The newer execution engine; its explain has `explainVersion: '2'` and lowercase stage names in `executionStages`. |
| pipeline | An aggregation's list of stages; the optimiser may move and merge stages before it runs. |
| keyset pagination | Paging by "rows after this sort key", with a filter on the last row's key, instead of `skip`. |
| dotted path | A field reference into a sub-document, such as `address.city`; `$set` of a dotted path changes only that field. |
| revision | A value that changes on every write (a counter `rev`, or Beanie's `revision_id`); a write filtered on it fails when someone wrote first. |
| write concern | How many members must confirm a write before it returns; the default on a replica set is `{w: 'majority'}`. |
| bucket | A document holding a bounded group of small items (readings of one device for one day), instead of one document per item or one unbounded array. |
| N+1 | One query for a list, then one more per item of the list. |
| Link | Beanie's reference to another document, stored as a DBRef (`{$ref, $id}`). |
| server case | Which server the task may touch: none, development, or production (`core/orient.md`). |
