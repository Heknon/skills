# mongomock: what it cannot show

mongomock 4.3.0 with PyMongo 4.18.2, *lab*. Decision M6: keep it where a
project already uses it for logic tests; never take it as proof of index
use, plans, speed, transactions or server errors. Test fixtures are the
pytest skill's; this is what mongomock gets wrong.

| Tried | mongomock | Real server (8.0.32) |
| --- | --- | --- |
| `cursor.explain()` | `AttributeError: 'Cursor' object has no attribute 'explain'` | the plan |
| `.hint("nope_1")` on a missing index | returns results | `hint provided does not correspond to an existing index` |
| `find({"name": "ann lee"}, collation={"locale": "en", "strength": 2})` | `[]`: collation ignored | matches "Ann Lee" and "ANN LEE" |
| `$indexStats` | `NotImplementedError` | counters |
| `start_session()` and a transaction | `NotImplementedError: Mongomock does not support sessions yet` | commits |
| `$set: {"address.city": ...}` on `{address: null}` | `modified_count` 0, no error | `WriteError: Cannot create field 'city' in element {address: null}` |
| `db.command("profile", 1)` | `TypeError` | profiler on |
| `client.bulk_write([...])` | `TypeError: 'Database' object is not callable` | works on 8.0 |
| unique index, second duplicate | `DuplicateKeyError` | same |
| `$regex` with `i`, `$lookup` | work | work |

So a test suite green on mongomock says nothing about the dotted-`$set`
rules (`core/patch-to-set.md`), collations, transactions or any plan.
Those tests run against a development server (a replica set), selected
by an environment variable as the recipes do (`MONGODB_URI`).
