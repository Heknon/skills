# Transactions

**Verdict you produce:** whether the operation needs a transaction, and
if so the code and what it costs.

```
operation:  <what must happen together>
needs one:  <no: one document (atomic by itself) | no: idempotent upserts | yes: several documents must change together>
topology:   <replica set or sharded; a standalone cannot>
code:       <with_transaction callback, read/write concern>
cost:       <documents held, lifetime limit, conflicts retried>
```

The architecture skill owns which layer starts and ends a transaction
(unit of work); this file owns what a Mongo transaction is and costs.

## 1. Do you need one?

| Case | Needs a transaction? |
| --- | --- |
| change one document, any number of its fields | no: a single-document write is atomic |
| a counter or state change guarded by a condition | no: put the condition in the filter (`{_id, status: "open"}`) and check `matched_count` |
| a PATCH guarded by a revision | no (`core/patch-to-set.md`) |
| a re-runnable import | no: upserts with a unique key (`core/writes.md`) |
| move money between two accounts; an order and its stock reservation must both happen or neither | yes |

A transaction around a single `update_one` adds a session, a commit and
retry handling, and changes nothing about atomicity.

## 2. Topology

*lab*: on a standalone 8.0.32 server, the first write inside a
transaction failed: `OperationFailure: Transaction numbers are only
allowed on a replica set member or mongos` (code 20, `IllegalOperation`).
The same code committed on a single-node replica set. Development
servers should run as a replica set (`mongod --replSet rs0`, then
`rs.initiate()`), even with one member.

## 3. The code

```python
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

def transfer(session):
    accounts.update_one({"_id": "a"}, {"$inc": {"bal": -5}}, session=session)
    accounts.update_one({"_id": "b"}, {"$inc": {"bal": 5}}, session=session)

with client.start_session() as s:
    s.with_transaction(transfer, read_concern=ReadConcern("snapshot"),
                       write_concern=WriteConcern("majority"))
```

Every operation inside takes `session=`; one without it runs outside the
transaction. `with_transaction` retries the callback on errors labelled
`TransientTransactionError` and the commit on
`UnknownTransactionCommitResult`, and stops retrying after 120 seconds
(PyMongo 4.18.2 docstring of `ClientSession.with_transaction`). So the
callback must be safe to run again (no side effects outside the
database), and must not catch and hide command errors. Async: the same API on
`AsyncMongoClient` with `await` (`pymongo/clients.md`).

### Beanie, and `bind()`

A Beanie call takes the session the same way, `insert(session=s)`,
`find_one(..., session=s)`, and escapes the transaction without it.
*lab* (Beanie 2.2.0, PyMongo 4.18.2, 8.0.32 single-node replica set):
inside `start_transaction()`, one `insert(session=s)` and one
`insert()`, then `abort_transaction()`: the first was rolled back, the
second stayed stored.

PyMongo 4.17 added `AsyncClientSession.bind()` (and `ClientSession.bind()`
for the sync client): inside its block, every operation that gives no
session uses the bound one (a context variable, read in
`asynchronous/client_session.py`).

```python
async with client.start_session() as s:
    async with s.bind():
        async with await s.start_transaction():
            await Account(name="b", balance=3).insert()           # no session=
            await Account.find_one(Account.name == "a").update({"$inc": {"balance": 10}})
```

*lab*: with `abort_transaction()` at the end, neither the insert nor the
update was stored; without it, both committed, and a `find_one` inside
the block saw the insert before the commit. `bind()` ends the session
when its block exits (`end_session=True` by default; `s.has_ended` was
`True` after it). Prefer `session=` on every call where the code
already passes it; `bind()` suits code whose calls you cannot all
reach. Check the installed PyMongo first (`uv pip show pymongo`):
before 4.17 there is no `bind()`. Which layer opens the session and the
transaction is the architecture skill's (unit of work).

## 4. What it costs (*lab*, 8.0.32)

- **Write conflicts**: two transactions updating the same document: the
  second failed at once with `WriteConflict` (code 112), labels
  `['TransientTransactionError']`; `with_transaction` would retry it.
- **Held documents block other writers**: while a transaction held
  document `a`, a plain `update_one` on `a` outside any transaction
  waited until the client's 1.5 s timeout (`NetworkTimeout`). It waits
  until the transaction commits or aborts.
- **Lifetime**: `transactionLifetimeLimitSeconds` is 60. With it set to
  2, a transaction kept open for 6 s failed at commit: `NoSuchTransaction`
  (code 251), `Transaction with { txnNumber: 1 } has been aborted.`
  `maxTransactionLockRequestTimeoutMillis` is 5.

Keep transactions short: no network calls, no user input, no slow
computation inside the callback.

## Never

- Never wrap a single-document write in a transaction "to be safe".
- Never call another service inside a transaction.
- Never promise transactions on a standalone server.
- Never leave a call inside a transaction without `session=` (or a
  `bind()` block around it): it commits on its own, whatever happens to
  the transaction.
