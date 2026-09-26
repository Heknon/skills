# SQLAlchemy errors and their translation

*lab* SQLAlchemy 2.1.1 on aiosqlite; asyncpg read in source.

| Case | Raised | Tell it apart by |
| --- | --- | --- |
| unique violation, aiosqlite | `sqlalchemy.exc.IntegrityError`; `e.orig` is `sqlite3.IntegrityError`; message `UNIQUE constraint failed: customers.email` | `"UNIQUE constraint failed" in str(e.orig)` |
| unique violation, asyncpg | `sqlalchemy.exc.IntegrityError`; `e.orig` is the dialect's `UniqueViolationError` (a subclass of its `IntegrityError`), mapped from `asyncpg.exceptions.UniqueViolationError` | `e.orig.sqlstate == "23505"` (also `pgcode`), set in `sqlalchemy/dialects/postgresql/asyncpg.py` (`Error.__init__`); *not run on PostgreSQL* |
| foreign key, not null, check (asyncpg) | `IntegrityError` with `orig` `ForeignKeyViolationError`, `NotNullViolationError`, `CheckViolationError` | `sqlstate` |
| attribute read needing IO | `StatementError` wrapping `MissingGreenlet` | `loading.md` |
| `begin()` inside an open transaction | `InvalidRequestError: A transaction is already begun on this Session.` | `session.md` |

`IntegrityError`'s MRO (*lab*): `IntegrityError`, `DatabaseError`,
`DBAPIError`, `StatementError`, `SQLAlchemyError`.

## Where it is raised: at the flush

The INSERT runs at `flush()` (or at `commit()` if nothing flushed
first). The repository flushes after `add`, so the error is raised in
the repository method that knows what it means:

```python
try:
    await self.session.flush()
except IntegrityError as exc:
    if _is_unique_violation(exc):
        raise DuplicateAccountError(owner_email) from exc
    raise
```

A check that covers both drivers, from the recipe:

```python
def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    return sqlstate == "23505" or "UNIQUE constraint failed" in str(exc.orig)
```

Re-raise anything else unchanged: a foreign-key failure is not a
duplicate. The `IntegrityError` inside `session.begin()` rolls the
transaction back on its way out.

A codebase that commits in a dependency gets the error at that commit,
after the route returned: nothing can translate it there, which is one
more reason to flush in the repository (*lab:* the client saw 201 with
the default scope, `core/transactions.md`).
