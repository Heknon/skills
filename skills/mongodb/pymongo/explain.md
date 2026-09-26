# Explain from Python

PyMongo 4.18.2, MongoDB 8.0.32, *lab*.

## Choose the verbosity yourself

`Cursor.explain()` sends no verbosity, so the server uses its default,
`allPlansExecution` (*lab*: the command sent was `{"explain": {"find":
"orders", ..., "limit": 20, "singleBatch": true}}`, and the result had
`executionStats.allPlansExecution`). The source says: "To use a
different verbosity use `Database.command` to run the explain command
directly."

```python
plan = db.command(
    "explain",
    {"find": "orders", "filter": q, "sort": {"created_at": -1}, "limit": 20},
    verbosity="executionStats",
)
plan = db.command(
    "explain",
    {"aggregate": "orders", "pipeline": pipeline, "cursor": {}},
    verbosity="executionStats",
)
```

Async: `await db.command(...)` and `await cursor.explain()` on
`AsyncMongoClient`.

## Beanie has no explain

Record the command Beanie sends (command monitoring,
`pymongo/clients.md`) and explain that: a `find` becomes `{"find": ...}`
with its filter, sort, limit and projection; `fetch_links=True` and
`count()` become `aggregate` pipelines (`beanie/queries.md`).

## Save it, read it later

```python
from bson import json_util
Path("explain.json").write_text(json_util.dumps(plan, indent=1))
```

`uv run --no-sync python <skill>/recipes/explain_report.py --file
explain.json` summarises a saved explain; from mongosh, save one with
`EJSON.stringify(db.orders.find(q).explain("executionStats"))`.

## What `explain_report.py` prints

*lab*, the ESR index:

```
server:          8.0.32
namespace:       shop.orders
explainVersion:  1
winning plan:    LIMIT <- FETCH <- IXSCAN
  index:         status_1_created_at_1_total_cents_1 {"status": 1, "created_at": 1, "total_cents": 1} multikey=False
  bounds:        {"status": ["[\"paid\", \"paid\"]"], "created_at": ["[MaxKey, MinKey]"], "total_cents": ["[inf.0, 10000]"]}
rejected plans:  0
nReturned:       20
keys examined:   20
docs examined:   20
time ms:         1
per returned:    keys 1.0, docs 1.0
covered:         no
verdict:         fine
```

For a `$group` or count it says `summarising: yes` and does not use the
per-returned ratios (a count returns one document for 49,951 keys).
