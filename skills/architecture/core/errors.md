# Errors across the layers

**Verdict you produce:** for each failure, where it is raised, where it
is translated, and the response a client sees, with a test per status.

```
failure:     <what goes wrong>
raised:      <driver error or domain error, path>
translated:  <repository path: driver -> domain | none needed>
response:    <category handler -> status and body>
test:        <test per status code, run line>
```

Which classes to define and their fields: `placement/custom-errors.md`.
The response body and status codes: the api skill
(`skills/api/core/errors.md`, `fastapi/errors.md`).

## One translation per boundary

```
driver error  --repository-->  domain error  --one handler per category-->  response
DuplicateKeyError              DuplicateAccountError(ConflictError)         409
IntegrityError                 DuplicateAccountError(ConflictError)         409
(no row)                       AccountNotFoundError(NotFoundError)          404
```

- **Repository**: catch the narrowest driver error at the call that
  raises it (for SQL, the `flush()` that runs the INSERT, not a later
  commit), and `raise DomainError(...) from exc`. Nothing above imports
  the driver's exceptions.
- **Service**: raises domain errors for rule failures
  (`InsufficientFundsError`); lets the repository's pass through; knows
  no HTTP.
- **Edge**: one handler per category registered in the app factory.
  *lab,* Starlette 1.7.0: a handler registered for a base class caught
  every subclass (`NotFoundError` 404 caught `OrderNotFoundError`), and
  with handlers for several classes in one MRO the nearest class won
  whatever the registration order: `AppError` then `NotFoundError`, or
  the reverse, both gave 404 for `OrderNotFoundError` and 500 (the
  `AppError` handler) for `ConflictError`; adding a handler for
  `OrderNotFoundError` itself gave it that one. The lookup walks
  `type(exc).__mro__` (`starlette/_exception_handler.py:16`). So a new specific error needs
  no new handler; a new category does.
- A worker or CLI catches the base or a category by type
  (`except AppError`), never `HTTPException`.

## Translated twice, or not at all (L8)

| Seen | Problem |
| --- | --- |
| `except IntegrityError` in a route | every route and worker repeats it and imports the driver |
| `raise HTTPException(409)` in a repository | a worker gets an HTTP error; the repository knows HTTP |
| a domain error caught in the service and re-raised as another domain error of the same meaning | translated twice; one of them goes |
| `except Exception: raise NotFoundError` | a broad catch turns every bug into a 404 |
| no translation | a duplicate key is a 500 |

## Driver error classes

| Database | Duplicate key raises (*lab* unless marked) | File |
| --- | --- | --- |
| MongoDB via Beanie `insert()` | `pymongo.errors.DuplicateKeyError` (code 11000; `details` has `keyPattern`, `keyValue`) | `beanie/errors.md` |
| SQLAlchemy on aiosqlite | `sqlalchemy.exc.IntegrityError`, `orig` `sqlite3.IntegrityError: UNIQUE constraint failed: <table>.<column>` | `sqlalchemy/errors.md` |
| SQLAlchemy on asyncpg | `sqlalchemy.exc.IntegrityError`, `orig.sqlstate == "23505"` (read in source, *not run on PostgreSQL*) | `sqlalchemy/errors.md` |

## Raising

- `raise DomainError(...) from exc` at a translation point: the log
  shows the driver's message under "The above exception was the direct
  cause". ruff `B904` flags a `raise` in an `except` without `from`.
- `from None` only when the cause would leak internals to a place that
  prints it.
- `except Exception` only at the outermost edge (the unhandled-error
  handler, a job runner that reports failures); ruff `BLE001` flags it
  elsewhere.
- Add context without a new class: `e.add_note("while importing row
  12")` (3.11 and later; *lab,* 3.12.14: the note printed under the
  message in the traceback).

## Tests

One test per status the feature can return, through `TestClient`, plus
one for the translation itself at the repository with a real database:

```python
with pytest.raises(DuplicateAccountError) as info:
    run_db(scenario)
assert type(info.value.__cause__).__name__ == "IntegrityError"
```

(*lab:* removing the translation failed it.)
