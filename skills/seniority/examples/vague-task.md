# Worked example: a vague ask, scoped, measured, and challenged

Follow this when the ask is large or vague: "make it faster", "clean this
up", "improve the tests". Copy the order of the moments and the shape of
the ledger lines. Change the facts, not the shape.

## The ask

> Search is slow. Make it faster.

## Start

**Scope** (`core/scope.md`). "Faster" has no number, so `done when` needs
one. It cannot be invented: the person owns the target. But one cheap look
might answer it (a ticket, a stated SLO), so look first, and ask only if
nothing is written. The measurement itself can be fixed now: the same
query, the same data, before and after.

```
goal: "Search is slow. Make it faster."
done when: p95 of `GET /search?q=pump` over 200 runs on the dev dataset, measured before and after, meets the target the person gives
budget: 40 steps
scope out: indexing speed, the search UI
```

**Assumptions**:

- A1: "search" means the `/search` endpoint, not the admin search page.
  Likely, cheap to check (one route file).
- A2: the dev dataset is large enough to show the slowness. If false, every
  measurement is wrong. Check before measuring.

**First step** (`core/first-step.md`): large and vague, so find the entry
point, the route that serves the request.

## The work

Steps 1 and 2 find the route and check the dataset size. Step 3 looks for
a written target and finds none. Step 4 asks, with a recommendation. The
person answers with a target: under 300 ms.

Step 5 measures: p95 is 1.9 s. Step 6 profiles one request: 85 percent of
the time is in `rank_results`, which loads every document's full text.

**Choose** (`core/trade-offs.md`). Three options:

- add a cache in front of search;
- load only the fields `rank_results` reads;
- move ranking into the database query.

The cache does not make the first request faster, and adds invalidation
work later. Moving ranking to the database touches the schema and is hard
to undo. Loading fewer fields is one function, reversible, and the profile
(observed) points straight at it.

**Challenge** (`core/challenge.md`) the chosen plan:

1. Pre-mortem: it failed because `rank_results` also reads a field not in
   the reduced list, and results change silently.
2. Counter-case: a query that matches a document whose snippet uses the
   body text.
3. Simplest alternative: this is already the smallest.
4. Load-bearing assumption: the ranking output is identical with fewer
   fields. Not verified; one step verifies it.
5. What would change my mind: any difference in ranked ids for the test
   queries.

Verdict: proceed with a change: compare ranked ids before and after on
the 20 queries in the test suite. Step 7 captures the baseline ids.

Steps 8 to 10: change, compare the ids (identical), measure again: p95 is
240 ms.

## The ledger

```markdown
# Ledger

goal: "Search is slow. Make it faster."
done when: p95 of `GET /search?q=pump` over 200 runs on the dev dataset, measured before and after, meets the target the person gives
budget: 40 steps
scope out: indexing speed, the search UI

## Assumptions

- A1 [verified at step 1] "search" means the /search endpoint
- A2 [verified at step 2] the dev dataset is large enough to show the slowness
- A3 [verified at step 9] ranking output is identical when only the ranked fields are loaded

## Hypotheses

none

## Steps

1. action: search "/search" in api/routes/ | result: api/routes/search.py:14 def search(q) | new fact: /search is served by api/routes/search.py
2. action: `python manage.py count_documents --env dev` | result: 184312 documents | new fact: dev has 184312 documents, close to production's size
3. action: search "latency" and "SLO" in docs/ and the open tickets export | result: no target stated | new fact: no written target exists
4. action: ask: what p95 should /search reach? I recommend under 300 ms, the budget other read endpoints meet | result: person: under 300 ms | new fact: the target is p95 under 300 ms
5. action: `python tools/bench.py /search?q=pump --runs 200` | result: p50 1.2 s, p95 1.9 s | new fact: the baseline p95 is 1.9 s
6. action: `python tools/bench.py /search?q=pump --runs 1 --profile` | result: rank_results 85% of time, Document.load_full 80% of that | new fact: loading full documents in rank_results dominates
   verdict trade-offs: load only the ranked fields because the profile points at it and it is one function; not a cache because the first request stays slow; not ranking in SQL because it changes the schema and is hard to undo
   verdict challenge: proceed with a change: compare ranked ids on the test queries because 4: identical ranking is not verified
7. action: `python tools/rank_snapshot.py --queries tests/search_queries.txt --out before.json` | result: 20 queries, ids written | new fact: baseline rankings are captured
8. action: edit search/rank.py rank_results to call Document.load_fields(RANK_FIELDS) | result: 6 lines changed | new fact: rank_results now loads 3 fields instead of the full document
9. action: `python tools/rank_snapshot.py --queries tests/search_queries.txt --out after.json --compare before.json` | result: 20 of 20 identical | new fact: rankings are unchanged
10. action: `python tools/bench.py /search?q=pump --runs 200` | result: p50 150 ms, p95 240 ms | new fact: p95 is 240 ms, under the 300 ms target

## Done

observed at step 10: p95 240 ms over 200 runs on the dev dataset, target under 300 ms, baseline 1.9 s
```

## The answer

```
/search spent 85 percent of its time loading full documents to rank them
(step 6). rank_results now loads only the three fields it ranks on
(search/rank.py). Rankings are identical for all 20 test queries (step 9).
p95 on the dev dataset went from 1.9 s to 240 ms over 200 runs (steps 5 and
10), under your 300 ms target.

## Done when
p95 of GET /search?q=pump over 200 runs on the dev dataset meets the
target: observed at step 10, 240 ms against under 300 ms.

## Not done
- Measured on one query, q=pump; other query shapes were not benchmarked.
- Indexing speed and the search UI (scope out).

## Unverified
none

## Ledger check
OK: PASS=13; exit 0
```
