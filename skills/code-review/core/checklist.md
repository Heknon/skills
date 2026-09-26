# Checklists: which ones, one pass each

**Verdict you produce:** the passes run, and for each its findings or
`none`, with the leads you opened and set aside.

```
passes:    correctness, errors, edge-cases (always); security, api-contract, architecture (a route changed); tests
leads:     14 from review_diff.py signs; 3 kept as findings, 11 set aside (read, not a problem)
verdict checklist: <findings: EDG1 src/library/reviews.py:14, ... | none in <passes>>
```

## Which passes (CR7)

Always: `checklists/correctness.md`, `errors.md`, `edge-cases.md`, and
`tests.md` for the changed behaviour. Add by what the change touches:

| The diff touches | Add |
| --- | --- |
| a route, a dependency, a request or response model, a status code | `api-contract.md`, `security.md`, `architecture.md` |
| a query, a write, a stored document, an index | `data.md`, `concurrency.md` |
| shared state: a module-level object, a counter, an amount, stock | `concurrency.md` |
| `async def` code | `concurrency.md` (CON2) |
| a pydantic model, a validator, settings | `models.md` |
| a service, a repository, an exception class, a transaction | `architecture.md` |
| code that reads request data, files, messages or environment | `security.md` |

## One pass at a time

1. **Get the leads** once for the whole diff:

   ```
   uv run --no-sync python <skill>\recipes\review_diff.py signs $env:TEMP\review.diff
   ```

   Each line is `path:line  ID  text`: the line matched a sign of that
   checklist item. `TST` signs read test files; the others read the
   rest. A lead is not a finding. *lab, measured on fourteen seeded
   changes:* the signs hit the planted line in nine of the ten with a
   bug inside the diff; they missed a leaked field (found by
   architecture's L3 search) and cannot see a broken caller outside the
   diff (`core/callers.md`). On three clean changes they gave 0, 3 and 6
   leads, none of them a finding.
2. **For each pass, read every hunk with only that checklist's
   questions**, then open the leads of its IDs. Signs miss most logic
   bugs: the reading is the pass, the leads are a reminder.
3. **Each suspicion becomes a finding or is dropped**, in the pass.
   A finding has `path:line` and a scenario (`output/format.md`);
   without a line it is not reported; without a scenario it is at most
   a nit.
4. **Domain questions go to their owner.** A checklist item that names
   another skill's file is answered from that file, or from a run,
   never from memory. A claim that a library call is wrong is settled
   in the installed source (offline-docs: `core/behaviour.md`,
   `core/signature.md`) before it is written. *lab:* a model that
   remembers Motor as "the async MongoDB driver" would call
   `from pymongo import AsyncMongoClient` wrong; PyMongo 4.18.2 defines
   it at `pymongo/asynchronous/mongo_client.py:167` and exports it at
   `pymongo/__init__.py:93`. A name that is new, renamed or deprecated
   in the installed version is exactly where memory is wrong.
5. **Challenge each blocker and major** before it is written: seniority
   `core/challenge.md`, question 2 (a concrete input) and question 6
   (what else would explain it). A blocker that fails the challenge is
   ranked by what is left.

## What a pass does not do

- It does not repeat another pass: a finding lives in the first pass
  that finds it, and the others do not list it again.
- It does not propose a redesign. The smallest fix goes in `suggest:`;
  a restructuring is named for later (refactoring skill).
- It does not open files the scope left out without saying so.
