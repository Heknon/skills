# Testing a Beanie service

| Test | Needs | How |
| --- | --- | --- |
| service rules | nothing | the service with a fake unit of work (`recipes/beanie_service/tests/conftest.py`) |
| routes | nothing | `create_app(connect=False)` and an override of `get_account_service` |
| repository, unit of work | a replica set | `MONGODB_URI`; skip without it |
| wiring | a replica set | one request through the real app, no override |

## Why the fake returns domain models

A Beanie 2.2.0 `Document` cannot be built before `init_beanie`: *lab,*
`User(email=..., password_hash=...)` raised
`beanie.exceptions.CollectionWasNotInitialized`. A fake repository that
returns documents therefore needs a server; one that returns domain
models does not. So the fake keeps the repository's contract with
domain models and domain errors, and a `transaction()` that restores
its data when the block raises.

## Why routes need `connect=False`

The lifespan runs `init_beanie`, which talks to the server; overriding
a provider does not skip the lifespan. The recipe's
`create_app(connect=False)` builds the app without it for route tests.

## The server

Run the repository tests against a replica set (a single node is
enough); on a standalone server the transaction tests fail. Skip, do not
fail, when `MONGODB_URI` is missing, from a fixture:

```python
@pytest.fixture
def run_db():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        pytest.skip("set MONGODB_URI to a replica set to run the repository tests")
```

*lab:* `pytest.skip(..., allow_module_level=True)` at the top of the
tests' `conftest.py` did not skip: pytest 9.1.1 printed a traceback
ending in `Skipped: set MONGODB_URI` and exited 1 without running a
test. Skip in a fixture or a test module instead.

mongomock's limits are the mongodb skill's (`pymongo/mongomock.md`); the
recipes do not use it.

## Runs (*lab*)

```
uv run pytest -q                        9 passed, 6 skipped   (no MONGODB_URI)
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
uv run pytest -q                        15 passed
```

The PowerShell line is *not run on Windows*; the lab set the variable in
bash.
