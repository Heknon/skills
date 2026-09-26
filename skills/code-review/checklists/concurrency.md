# Concurrency

Run when the change writes shared state (a database, a module-level
object, a file) or touches `async def` (`core/checklist.md`). A server
runs many requests at once: FastAPI runs `def` routes in a thread pool
and `async def` routes on one event loop (api: `fastapi/concurrency.md`
has the lab numbers). Single-threaded tests cannot show these bugs.

### CON1 Read, modify, write back

- **Ask:** does the code read a value, compute a new one in Python and
  write it back? Two requests that read the same value both write their
  result, and one is lost.
- **Sign:** `find_one` or `get` then `$set` of a computed value;
  `doc.count += 1` then `save()`; a removed `$inc`.
- **Scenario (lab, MongoDB 8.0.32, PyMongo 4.18.2):** `find_one`, add
  1, `update_one` with `$set`: 1000 increments from 16 threads stored
  109, 109 and 123 in three runs; `find_one_and_update` with `$inc`
  stored 1000 each time. Write it as the interleaving: A reads 41, B
  reads 41, A writes 42, B writes 42; one increment lost.
- **Severity:** major; blocker for money, stock or points.
- **Facts:** mongodb (`core/writes.md`: an operator instead of
  read-add-write; `beanie/writes.md`: `save()` on a stale copy loses
  other writes; revisions).

### CON2 A blocking call inside `async def`

- **Ask:** does an `async def` route or dependency call something that
  waits without `await`: `time.sleep`, `requests`, a sync database
  driver, a large file read?
- **Severity:** major when it stalls every request under load.
- **Facts:** api (`fastapi/concurrency.md`: how to find the call and
  the three fixes).

### CON3 Check, then act

- **Ask:** is there an `if not exists: insert` or `if stock >= n:
  reserve` whose check and act can be split by another request?
- **Severity:** major when it creates duplicates or overdraws.
- **Facts:** mongodb (`core/writes.md`: concurrent upserts and the
  unique index; `core/transactions.md`).

### CON4 Module-level state changed per request

- **Ask:** does a request change a module-level dict, list or client
  that other requests or threads share?
- **Sign:** `global`; a module-level `{}` or `[]` written in a function.

### CON5 Writes that must happen together

- **Ask:** if the second of two writes fails, is the first undone? Who
  owns the transaction?
- **Facts:** architecture (L5, `core/transactions.md`) decides which
  layer owns it; mongodb (`core/transactions.md`) says what a Mongo
  transaction needs and costs.

## Signs

```
CON1  +  \$set\b.*[-+]\s*1\b|\+=\s*1\b|\.save\(\)|^\s*\w+\s*=\s*\w+\[["']\w+["']\]\s*[-+]
CON1  -  \$inc\b|find_one_and_update\(
CON2  +  time\.sleep\(|\brequests\.(get|post|put|patch|delete)\(|urlopen\(
CON3  +  ^\s*if\s+(not\s+)?(await\s+)?\w+(\.\w+)*\.(find_one|exists|count_documents|get)\(
CON4  +  ^\s*global\s
CON5  +  \.(insert_one|insert_many|update_one|update_many|delete_one|replace_one)\(
```
