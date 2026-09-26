# A Beanie 2 service's database layer

Beanie 2.2.0 on PyMongo 4.18.2's `AsyncMongoClient`, MongoDB 8.0.32.
What each piece sends is asserted by the tests, which record commands
with PyMongo command monitoring.

| File | What it is |
| --- | --- |
| `app/models.py` | `Customer` (`use_revision`, a unique index), `Order` (a `Link`, a compound index), `CustomerCard` (a projection model) |
| `app/db.py` | `init_db(uri, db, build_indexes=False)`: startup with `skip_indexes=True` |
| `app/queries.py` | `recent_orders` (two commands, no N+1), `customer_cards` (projection), `patch_customer` (dotted `$set` on the revision, `Conflict`), `add_points` (`$inc`) |
| `build_indexes.py` | the one-off index job: `init_beanie` with index creation on |
| `tests/conftest.py` | the command listener; skips every test without `MONGODB_URI` |
| `tests/test_app.py` | ten tests: no index commands at startup, the index job, 2 commands vs 51 (N+1), `fetch_links` puts `$lookup` before `$sort`, projection, the revision-guarded patch and its conflict, `save()` sends every field, `inc` |

The tests use `asyncio.run` and need no pytest plugin. Where this code
sits in a service (a repository, a unit of work) is the architecture
skill's call.

*lab*: 10 passed with `MONGODB_URI` set, through `uv run pytest` in a
fresh copy. The tests can fail: switching `recent_orders` to
`fetch_links=True`, `patch_customer` to `save()`, and startup to
`skip_indexes=False` failed 4 of them.
