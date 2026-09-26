# Who owns the transaction

**Verdict you produce:** the layer that begins and ends the
transaction, the unit of work, and a test that shows the rollback.

```
use case:  <the writes that must happen together>
owner:     <service, through uow.transaction() | a yield dependency (card) | none needed: one document>
unit:      <SqlUnitOfWork / MongoUnitOfWork, or the card's equivalent>
test:      <a test where the second write fails and the first is undone>
run:       <summary line>
```

## The rule (decision AR4)

One layer owns it: the **service**, which enters the unit of work
explicitly around the use case. Repositories flush and never commit;
routes never commit or roll back; no repository opens its own session.

```python
async def transfer(self, source_id, target_id, amount_cents):
    async with self.uow.transaction():            # begin
        source = await self.uow.accounts.get(source_id, for_update=True)
        ...
        await self.uow.accounts.set_balance(source_id, ...)
        await self.uow.accounts.set_balance(target_id, ...)
                                                  # commit, or rollback on an exception
```

## What goes wrong otherwise (*lab*)

| Arrangement | Result |
| --- | --- |
| each repository method commits (sandbox transfer, SQLAlchemy 2.1.1, aiosqlite) | a transfer to a frozen account answered 409 and the debit stayed: `assert 7500 == 10000` |
| the same, plus `await session.rollback()` in the route's `except` | unchanged: the debit was already committed |
| SQL write with no `transaction()` in the service (recipe mutant) | the insert was never committed: the next read raised `AccountNotFoundError: account 1 not found` |
| commit after `yield` in a request-scoped dependency, the INSERT failing at that commit | the client got **201**, the row was not stored; with `Depends(..., scope="function")` the client got 500 |
| Mongo writes inside `start_transaction()` without `session=` (PyMongo 4.18.2) | the write was outside the transaction and survived the abort |

The yield-dependency timing is the api skill's
(`skills/api/fastapi/dependencies.md`, "When the code after yield
runs"); the lab reran it with SQLAlchemy for the row above.

## Where the codebase commits in a dependency

Accept it (decision AR4) when the card says so, with two checks:

1. The dependency is `Depends(get_session, scope="function")` (FastAPI
   0.121.0 and later), so the commit runs before the response; with the
   default scope a client can be told 201 for a write that was rolled
   back.
2. Nothing else commits: no repository method, no route.

Then one request is one transaction, and a use case that needs two
transactions (rare) cannot be written; say so if the task needs one.

## One document in MongoDB needs no transaction

A single-document write is atomic; the mongodb skill's
`core/transactions.md` says when a transaction is needed and what it
costs. So the Beanie recipe's service opens a transaction only for the
transfer, not for `open_account` or `get`, while the SQL recipe's
service wraps every use case (every SQL statement runs in a transaction,
and without a commit it is lost). The unit of work is the same idea;
where the service uses it differs by database.

## The unit of work per database

- SQLAlchemy: `sqlalchemy/unit-of-work.md` (`async with
  session.begin()`; repositories flush).
- Beanie: `beanie/sessions.md` (a client session, `start_transaction()`,
  `session=` on every call; a replica set).

## Test the rollback

Two tests, both in the recipes:

- **service, with the fake**: tell the fake to fail the second write;
  assert the first is undone (`test_failed_second_write_undoes_the_first`).
  *lab:* removing the service's `transaction()` made it fail.
- **repository, with the real database**: write, then fail, inside one
  `transaction()`; read in a new session; assert the old value
  (`test_failed_transfer_rolls_back_the_first_write`).

A test that only checks the success path cannot tell one owner from
three.
