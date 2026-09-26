# Worked example: a Beanie list with N+1 queries

Kinds: Beanie, Diagnose. Beanie 2.2.0, PyMongo 4.18.2, MongoDB 8.0.32;
development data: 2,000 customers, 200,000 orders with `Link[Customer]`,
index `status_1`.

## The ask

> GET /orders/recent is slow. Make `recent_orders` faster.

```python
orders = await Order.find(Order.status == status).sort(-Order.created_at).limit(50).to_list()
for order in orders:
    await order.fetch_link(Order.customer)
    rows.append({..., "customer": order.customer.name})
```

## Steps

1. **Count the commands** (`pymongo/clients.md`: a `CommandListener` on
   the client): **51 commands, 0.113 s**: one `find`, then per order an
   `aggregate [{$match: {_id}}, {$limit: 1}, {$project: ...}]` on
   customers.
2. **Try the obvious fix**, `fetch_links=True`: 1 command, but **0.828
   s**. The recorded pipeline starts with `$lookup` and has `$sort` and
   `$limit` after it; its explain: `$cursor` 50,178, `$lookup` 50,178,
   `$sort` 50 (`beanie/links.md`). Every paid order was joined before 50
   were kept.
3. **Two queries instead**:
   ```python
   orders = await Order.find(Order.status == status).sort(-Order.created_at).limit(50).to_list()
   ids = list({o.customer.ref.id for o in orders})
   names = {c.id: c.name for c in await Customer.find(In(Customer.id, ids)).to_list()}
   ```
   **2 commands, 0.049 s**; the first row was identical in all three
   versions (`{'id': '6ab75f7d0d81d1a96c73dae6', 'total_cents': 1512,
   'customer': 'Customer 744'}`).
4. **The index for the first query** (`core/index-design.md`): `status`
   E, `created_at` S: `{status: 1, created_at: -1}`, declared in
   `Order.Settings.indexes` and built by the index job, not at startup
   (`beanie/indexes.md`). Before it, the `find` used `status_1` and
   sorted in memory.

## The answer

```
## Result
recent_orders sent one query per order (fetch_link in the loop: 51
commands). It now sends two: the 50 orders, then one Customer.find with
$in on their ids. fetch_links=True was not used: Beanie joins before
sorting, so it looked up all ~50,000 paid orders (0.83 s). Declared
{status: 1, created_at: -1} on Order for the sort.

## Checked
- Command counts with a PyMongo CommandListener: 51 before, 2 after
  (fetch_links=True: 1 command, 0.828 s; explain: 50,178 lookups).
- Same rows before and after (first row compared; 50 rows each).

## Not checked
- The new index on production: to be built by the index job before
  release (core/index-live.md).
```
