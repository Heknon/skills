# The async session

SQLAlchemy 2.1.1 with the `asyncio` extra (it pulls `greenlet`), on
aiosqlite 0.22.1 in the lab; asyncpg 0.31.0 was installed and its
source read, *not run on PostgreSQL* (no server in the lab). The 2.0
line: the SQL recipe's 13 tests also passed on SQLAlchemy 2.0.54.

## One engine per process, one session per request

```python
engine = create_async_engine(url)                       # in the lifespan
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session                                   # closed after the request
```

(`recipes/sqlalchemy_service/app/db.py`.) The engine is created in the
lifespan and read from `app.state`; creating it does not connect (*lab:*
route tests ran with no database file created). The session is the
unit every repository of the request shares (`core/wiring.md`).

## Facts the procedures rely on (*lab*)

| Fact | Seen |
| --- | --- |
| `async_sessionmaker(engine)` expires objects on commit by default | `Session.kw` had `expire_on_commit: True`; reading an attribute after commit raised `MissingGreenlet` (`loading.md`) |
| the session begins a transaction by itself on the first statement (autobegin) | after one `select`, `in_transaction()` was `True` |
| `session.begin()` after autobegin fails | `sqlalchemy.exc.InvalidRequestError: A transaction is already begun on this Session.` so the unit of work must begin before any read |
| a session closed without commit discards its work | a flushed, uncommitted `Order` was `None` in the next session |
| `async with session.begin():` commits on exit and rolls back on an exception | the recipe's rollback test |
| after an `IntegrityError` at commit, the session is unusable until rolled back | `in_transaction()` `True`, `is_active` `False` |

## Choices, and why the recipe makes them

- `expire_on_commit=False`: objects read inside the unit of work stay
  readable after it. The repository still maps rows to domain models
  before returning (`repository.md`), so nothing reads a row later;
  this is a second guard.
- No commit in any provider: the service commits through the unit of
  work (`core/transactions.md`). A codebase that commits in a yield
  dependency needs `Depends(..., scope="function")` (FastAPI 0.121.0
  and later), or the client may get 201 for a write that did not happen.
- `create_all` only for tests and local runs (`CREATE_TABLES=1`); a real
  service uses migrations, which have no owner yet (roadmap R5).

## Sync SQLAlchemy in the same codebase

A `def` route with a sync `Session` runs in the threadpool and never
raises `MissingGreenlet`; switching one route to sync to escape the
error is not a fix (it mixes two engines and two session factories). A
codebase that is sync throughout follows the same layers with `Session`
and `session.begin()`.
