# Links and N+1

Beanie 2.2.0, MongoDB 8.0.32, *lab*. Commands recorded with PyMongo
command monitoring.

## What a Link is

`customer: Link[Customer]` is stored as a DBRef: *lab*, `{'customer':
DBRef('customers3', ObjectId('6ab7...')), 'status': 'paid', ...}`. A
loaded document holds a `Link` object until fetched; `order.customer.ref.
id` is the linked `_id` without a query.

## Three ways to load 50 orders with their customers

*lab*, 200,000 orders, 2,000 customers, index `status_1` only, `status
== "paid"` (about 50,000 match), newest 50:

| Code | Commands | Time |
| --- | --- | --- |
| `find(...).sort().limit(50)`, then `await o.fetch_link(Order.customer)` per order | 51 (1 `find` + 50 `aggregate`) | 0.113 s |
| `find(..., fetch_links=True).sort().limit(50)` | 1 `aggregate` | **0.828 s** |
| `find(...).sort().limit(50)`, then one `Customer.find(In(Customer.id, ids))` | 2 `find` | 0.049 s |

`fetch_links=True` sent one command and was the slowest. Its pipeline
starts with the join:

```
[{"$lookup": {"from": "customers", "localField": "customer.$id", "foreignField": "_id", "as": "_link_customer"}},
 {"$unwind": {"path": "$_link_customer", "preserveNullAndEmptyArrays": true}},
 {"$addFields": {"customer": {"$cond": ...}}}, {"$project": {"_link_customer": 0}},
 {"$match": {"status": "paid"}}, {"$sort": {"created_at": -1}}, {"$limit": 50}, {"$project": {...}}]
```

The server moved the `$match` ahead of the `$lookup`, but not the
`$sort`: the explain showed `$cursor` 50,178, `$lookup` 50,178, `$sort`
50. Every matching order was joined before the 50 were chosen. On
1,000,000 orders the same shape joined 49,951 orders in 950 ms for 20
rows, and an index on `{status: 1, created_at: -1}` did not change that
(`core/aggregation.md`).

Without `sort`, or with a filter only on the order's own fields and a
`limit`, `fetch_links=True` was cheap: the lookups ran only for the rows
returned (*lab*: 20 lookups for `limit(20)`).

## The pattern to use

```python
orders = await Order.find(Order.status == status).sort(-Order.created_at).limit(50).to_list()
ids = list({o.customer.ref.id for o in orders})
names = {c.id: c.name for c in await Customer.find(In(Customer.id, ids)).to_list()}
```

Two commands whatever the page size, each served by an index (`_id` for
the second). In `recipes/beanie_app/app/queries.py` with a test that
counts the commands.

A filter on a linked field (`Order.customer.country == "BE"`) puts the
`$match` after the join, where the server cannot move it: *lab*, 1,000,000
orders, `{"customer.tier": "gold", "customer.country": "BE"}` with
`limit(20)` joined 21,813 orders to return 20 (416 ms), and without a
limit it would join them all. Query the customers first, then the orders
with `In(Order.customer.id, ids)`, which sends `{"customer.$id": {"$in":
[...]}}` (*lab*); index `customer.$id` for it, and check both explains.

## Counting commands

`pymongo/clients.md` has the listener. A request's command count must
not grow with the number of rows it returns.
