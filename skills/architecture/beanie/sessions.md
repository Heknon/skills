# Sessions and transactions with Beanie

**Verdict you produce:** where the client session starts, which calls
carry it, and the rollback test.

What a Mongo transaction needs and costs (a replica set, write conflicts,
the 60-second lifetime, `with_transaction` retries) is the mongodb skill's
`skills/mongodb/core/transactions.md`. This file is the unit of work
around it.

## The unit of work

```python
class MongoUnitOfWork:
    def __init__(self, client: AsyncMongoClient) -> None:
        self._client = client
        self.session: AsyncClientSession | None = None
        self.accounts = BeanieAccountRepository(self)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self._client.start_session() as session:
            # commits on exit, aborts on an exception
            async with await session.start_transaction():
                self.session = session
                try:
                    yield
                finally:
                    self.session = None
```

On PyMongo 4.18.2's async client, `start_session()` is called without
`await` and used with `async with`; `start_transaction()` is a
coroutine whose result is the context manager, hence `async with await`
(read in `pymongo/asynchronous/client_session.py`; ran in the lab).

## What the lab showed (MongoDB 8.0.32 replica set)

| Code inside `start_transaction()` | After an exception in the block |
| --- | --- |
| Beanie calls with `session=s` | rolled back: balance 100 stayed 100 |
| Beanie calls without `session=` | **not rolled back**: 100 became 70 |
| Beanie calls without `session=`, inside `async with s.bind():` | rolled back, and a read without `session=` inside saw the uncommitted 70 |

`AsyncClientSession.bind()` is new in PyMongo 4.17 ("Bind this session
so it is implicitly passed to all database operations within the
returned context", its docstring). The recipe passes `session=`
explicitly instead: it works on every PyMongo 4 release, and a
reviewer can see it. Whether to use `bind()` is the mongodb skill's
call to document.

## Use it only for several documents

A single-document write is atomic without a transaction. The Beanie
recipe's service uses `transaction()` for the transfer only;
`open_account` and `get` call the repository directly, with
`session=None`. The same service over SQL wraps every use case
(`core/transactions.md`).

## On a standalone server

A transaction fails on its first write (the mongodb skill records
`Transaction numbers are only allowed on a replica set member or
mongos`). Development and CI servers run as a replica set of one:
`mongod --replSet rs0`, then `rs.initiate()`.
