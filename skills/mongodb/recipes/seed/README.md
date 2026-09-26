# Seed data

`seed.py` writes the same documents on every run (`random.Random(42)`,
ObjectIds built from a time and a counter), so explain output recorded
here can be reproduced elsewhere. It drops `customers`, `orders` and
`events` in the database it is given, and creates no index but `_id`.

| Collection | Default count | Fields | Built for |
| --- | --- | --- | --- |
| `customers` | 200,000 | `name` (a third upper-cased), `email`, `country` (skewed), `tier` (5% gold), `created_at` | case-insensitive search, `$lookup` |
| `orders` | 1,000,000 | `customer_id`, `status` (60% shipped, 20% paid, 15% cancelled, 5% pending), `country`, `total_cents`, `created_at` over 900 days, `items[]` (1 to 5, multikey), `address{street, city, zip}` | ESR, pagination, patches, aggregation |
| `events` | 500,000 | `device_id` (500 devices), `ts`, `kind`, `value` | buckets and time ranges |

```
uv run seed.py --uri "mongodb://127.0.0.1:27017/?replicaSet=rs0" --db shop
uv run seed.py --customers 20000 --orders 100000 --events 1000   # smaller
```

*lab*: defaults in 34 s on 8.0.32; the collection sizes
are in `core/orient.md`.
