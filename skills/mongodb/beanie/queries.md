# Queries in Beanie, and what they send

Beanie 2.2.0, PyMongo 4.18.2, MongoDB 8.0.32. Every command below was
recorded with PyMongo command monitoring (*lab*). Judge a Beanie query by
the command it sends: explain that command (`pymongo/explain.md`).

## Calls and commands

| Beanie | Command sent |
| --- | --- |
| `await Customer.get(oid)` | `find` on `_id` |
| `await Customer.find_one(Customer.email == e)` | `find` with `filter`, `projection` of every model field plus `revision_id`, `limit: 1`, `singleBatch: true` |
| `await Order.find(Order.status == s).sort(-Order.created_at).limit(50).to_list()` | `find` with `filter`, `sort: {created_at: -1}`, `limit: 50` |
| `.skip(10).limit(5)` | `find` with `skip: 10, limit: 5` (skip costs: `core/pagination.md`) |
| `await Order.find(q).count()` | `aggregate [{$match: q}, {$group: {_id: 1, n: {$sum: 1}}}]` |
| `await Order.find(q).update({"$inc": {Order.qty: 1}})` | one `update` with `multi: true` |
| `await Order.find(q).delete()` | one `delete` with `limit: 0` |
| `await Order.find(q, fetch_links=True).to_list()` | an `aggregate` with `$lookup` first (`beanie/links.md`) |
| `await Order.find(q).aggregate(pipeline, projection_model=M).to_list()` | `aggregate [{$match: q}, *pipeline, {$project: M's fields}]` |
| `await Order.aggregate(pipeline).to_list()` | `aggregate` with the pipeline as given; returns dicts |

## Field expressions or raw dicts (decision M7)

Use field expressions for finds: a misspelt field fails at once.

*lab*: `Customer.find(Customer.emial == "x")` raised `AttributeError:
emial`; `Customer.find({"emial": "x"}).count()` returned 0 and sent
`{"$match": {"emial": "x"}}`, a wrong answer with no error. Nested
fields: `Customer.address.city == "Lyon"` sends `{"address.city":
"Lyon"}`. Operators: `from beanie.operators import In` then
`In(Customer.id, ids)`.

Pipelines are raw dicts: Beanie does not check field names in them. Test
a pipeline against a development server and read its explain.

## Projections

Every find already sends a projection of the model's fields, so fields
the model does not declare are not transferred. For fewer fields, a
projection model:

```python
class CustomerCard(BaseModel):
    name: str
    email: str

cards = await Customer.find(Customer.address.city == city).project(CustomerCard).to_list()
```

*lab*: the `find` carried `projection: {"name": 1, "email": 1}` and
returned `CustomerCard` objects (`recipes/beanie_app/app/queries.py`).
`find(..., projection_model=CustomerCard)` is the same. With
`aggregate(..., projection_model=M)` Beanie appends a `$project` of M's
fields and validates each row as M.

## Getting the collection

`Order.get_pymongo_collection()` returns PyMongo's `AsyncCollection`
(Beanie 2.x; 1.x: `get_motor_collection()`), for what Beanie does not
wrap: `$indexStats`, `explain`, `bulk_write` of mixed operations. Where
that code lives (a repository) is the architecture skill's call.
