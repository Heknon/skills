# Checkout latency

p99 of POST /checkout went from 180 ms to 1.9 s after Tuesday's release.
Production database: `mongodb://app-ro:...@db1.prod.internal,db2.prod.internal,db3.prod.internal/shop?replicaSet=prod`
(the read-only account is in the vault as MONGO_RO_URI; the admin account
is MONGO_ADMIN_URI).
