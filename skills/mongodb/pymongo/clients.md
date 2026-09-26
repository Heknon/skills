# Clients: MongoClient, AsyncMongoClient, and Motor

PyMongo 4.18.2, Python 3.12, MongoDB 8.0.32, *lab*. Check the installed
version first: `uv pip show pymongo motor`.

## Which client

| Code | Client | Import |
| --- | --- | --- |
| scripts, jobs, diagnosis, sync web apps | `MongoClient` | `from pymongo import MongoClient` |
| asyncio services, Beanie 2.x | `AsyncMongoClient` | `from pymongo import AsyncMongoClient` |
| Beanie 1.x, older asyncio code | Motor's `AsyncIOMotorClient` | read it; do not add it to new code |

The async API was beta up to PyMongo 4.12 (*lab*: 4.10.1 and 4.12.1
docstrings say `This API is currently in beta`) and has no such warning
from 4.13.0. Motor 3.7.1's package description says: "Motor will be
deprecated on May 14th, 2026, one year after the production release of
the PyMongo Async driver. Critical bug fixes will be made until May
14th, 2027."

## Create one client per process

```python
client = MongoClient(os.environ["MONGODB_URI"])              # sync
client = AsyncMongoClient(os.environ["MONGODB_URI"])         # async, inside the event loop
db = client["shop"]
```

The client holds the connection pool; create it at startup and reuse it.
`MongoClient(uri, serverSelectionTimeoutMS=5000)` fails in five seconds
instead of the default when no server answers (`recipes/orient.py` does
this).

## The async API (*lab*)

```python
async with AsyncMongoClient(uri) as client:
    docs = await client.shop.orders.find(q, proj).sort("created_at", -1).limit(3).to_list()
    n = await client.shop.orders.count_documents(q)
    async for d in client.shop.customers.find({}, {"name": 1}).limit(5):
        ...
    async with client.start_session() as s:
        await s.with_transaction(callback)     # callback is async and takes the session
```

`start_session()` is a plain call returning a session used with `async
with`; `close()` is a coroutine (`await client.close()`). Every
operation and cursor method that reaches the server is awaited.

## Seeing what the driver sends

Command monitoring records every command: the way to count queries (N+1)
and to see what an ODM builds.

```python
from pymongo import monitoring

class Commands(monitoring.CommandListener):
    def __init__(self): self.sent = []
    def started(self, event): self.sent.append((event.command_name, event.command))
    def succeeded(self, event): pass
    def failed(self, event): pass

log = Commands()
client = AsyncMongoClient(uri, event_listeners=[log])   # or monitoring.register(log) before creating clients
```

`recipes/beanie_app/tests/conftest.py` uses it. Skip `hello` and
`endSessions`, which the driver sends on its own.

## Types PyMongo cannot store

*lab*: `Decimal` -> `InvalidDocument: cannot encode object:
Decimal('1.10')` (use `bson.Decimal128`); `uuid.UUID` -> `cannot encode
native uuid.UUID with UuidRepresentation.UNSPECIFIED` (pass
`uuidRepresentation="standard"` to the client); a plain `Enum` ->
`InvalidDocument`; a `str` enum and `datetime` are stored as is.
