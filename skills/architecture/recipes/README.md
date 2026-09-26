# Recipes: one accounts service, twice

The same small service over SQLAlchemy and over Beanie, laid out by
feature (decision AR2): open an account (409 on a duplicate owner), read
one (404), transfer money between two (409 on insufficient funds,
atomic). Copy the nearer one whole, rename the feature, delete what the
task does not need.

| File | `sqlalchemy_service/` | `beanie_service/` |
| --- | --- | --- |
| `app/errors.py` | base and categories | same |
| `app/accounts/errors.py` | feature errors, positional fields | same, ids `str` |
| `app/accounts/domain.py` | `Account` (frozen pydantic) | same, `id: str` |
| `app/accounts/schemas.py` | `AccountIn`, `AccountOut.from_domain`, `TransferIn` | same |
| `app/accounts/models.py` | `AccountRow` (mapped class) | `AccountDocument` (Beanie) |
| `app/accounts/repository.py` | `SqlAccountRepository`, `SqlUnitOfWork` | `BeanieAccountRepository`, `MongoUnitOfWork` |
| `app/accounts/service.py` | rules, `Protocol`s, every use case in `transaction()` | rules, `Protocol`s, only the transfer in `transaction()` |
| `app/accounts/dependencies.py` | session -> unit of work -> service | client -> unit of work -> service |
| `app/accounts/router.py` | three routes, `from_domain` | same |
| `app/db.py` | engine, sessionmaker, `get_session` | `init_db` (`skip_indexes`), `get_client` |
| `app/main.py` | app factory, lifespan, one handler per category | same, `create_app(connect=False)` for route tests |
| `tests/conftest.py` | the fake unit of work | same |
| `tests/test_service.py` | rules and rollback with the fake | same |
| `tests/test_routes.py` | HTTP mapping with an override | same |
| `tests/test_repository.py` | real database: SQLite, or `DATABASE_URL` | real replica set: `MONGODB_URI`, skipped without |

The service, schemas, router, errors and domain files differ between
the two only in the id type and in which use cases open a transaction:
that is the point of the layers.

## Run

```
cd <skill>\recipes\sqlalchemy_service
uv run pytest -q                     # 13 passed (SQLite)

cd <skill>\recipes\beanie_service
uv run pytest -q                     # 9 passed, 6 skipped
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
uv run pytest -q                     # 15 passed
```

*lab,* Python 3.12.14 in fresh copies: the SQL recipe 13 passed on
SQLAlchemy 2.1.1 and on 2.0.54 (aiosqlite 0.22.1); the Beanie recipe 15
passed against a MongoDB 8.0.32 single-node replica set. A plain
`uv run pytest` with no Python named picked CPython 3.14.7 (the
`requires-python` is `>=3.12`); both recipes passed there too. Pin the
interpreter the way the packaging skill says if it matters. With
`DATABASE_URL` pointing at PostgreSQL through asyncpg: *not run on
PostgreSQL* (no server in the lab). The PowerShell lines are *not run
on Windows*.

## The tests can fail (*lab*)

| Broken on purpose | Failed |
| --- | --- |
| SQL: the translation of `IntegrityError` removed | `test_duplicate_owner_becomes_a_domain_error`, `test_the_wiring_end_to_end` |
| SQL: `kyc_reference` added to `AccountOut` | `test_open_account_hides_internal_fields` |
| SQL: `commit()` added to `set_balance` | `test_failed_transfer_rolls_back_the_first_write` |
| SQL: `transaction()` removed from `transfer` | `test_failed_second_write_undoes_the_first` |
| SQL: `transaction()` removed from `open_account` | four repository tests: the insert was never committed |
| Mongo: `session=` removed from both calls of `set_balance` | the rollback test |
| Mongo: the transaction removed from the unit of work | the rollback test |
| Mongo: the translation of `DuplicateKeyError` removed | two tests |

Two mutants survived, and are equivalent: the SQL unit of work without
`session.begin()` but with a commit after `yield` (a session closed
without commit discards its work), and a Mongo `set_balance` without
`session=` on the update only (Beanie keeps the find's session).

## Lint and layer contracts

`ruff check --select E,F,I,B,UP,N,TRY,EM,BLE,PLC0415` and `ruff format
--check`: clean on both (ruff 0.16.9). Each `pyproject.toml` carries an
optional `[tool.importlinter]` block, for a project that already uses
import-linter: *lab,* `uv run --with import-linter==2.15 lint-imports`:
`Contracts: 2 kept, 0 broken.` Running ruff and import-linter in a
project is the linting skill's.
