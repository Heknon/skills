# Index types and options

**Verdict you produce:** which option the need calls for, the spec, and
the query that proves the planner uses it.

```
need:     <case-insensitive match | only some documents | expire | uniqueness | words | test before drop>
index:    <spec with options>
query:    <the query as it must be written to use it>
checked:  <explain: index name in the plan, keys and docs>
```

All *lab*, MongoDB 8.0.32. PyMongo: `coll.create_index(keys, **options)`;
mongosh: `db.coll.createIndex(keys, options)`.

## Which option for which need

| Need | Option | The catch |
| --- | --- | --- |
| match text in any letter case | `collation: {locale: "en", strength: 2}` | used only by queries with the same collation; `$regex` ignores collation |
| index only some documents (open orders) | `partialFilterExpression` | used only when the query implies the filter |
| unique, but many documents lack the field | `unique` with `partialFilterExpression: {f: {$type: "string"}}`, or `sparse` | a plain unique index counts a missing field as `null` |
| delete documents after a time | `expireAfterSeconds` on a date field | deletes about once a minute; ignores non-dates |
| search words | a `text` index | one per collection |
| test whether an index is still needed | `hidden: true` (collMod) | resets `$indexStats`; see `core/index-live.md` |

## Collation (case-insensitive)

```
db.customers.createIndex({name: 1}, {name: "name_ci", collation: {locale: "en", strength: 2}})
db.customers.find({name: "ann lee"}).collation({locale: "en", strength: 2})
```

*lab*, 200,000 customers:

| Query | Index used | Keys | Returned |
| --- | --- | --- | --- |
| `{name: {$regex: "^ann lee$", $options: "i"}}` | `name_1`, bounds `["", {})` | 200,000 | 828 |
| `{name: "ann lee"}` with the collation | `name_ci`, bounds `CollationKey(0x2943...)` | 828 | 828 |
| `{name: "Ann Lee"}` without a collation, only `name_ci` exists | COLLSCAN | 0 (200,000 docs) | 534 |
| `{name: {$regex: "^ann"}}` with the collation | `name_1` (simple collation), case-sensitive | 0 returned | 0 |

So: the query must pass the same collation. A collection created with a
default collation (`db.createCollection("cc", {collation: {locale: "en",
strength: 2}})`) gives it to every query and to new indexes: *lab*,
`find({name: "ann lee"})` with no collation matched "Ann Lee" and "ANN
LEE" through an IXSCAN with collation-key bounds. For prefix search
in any case, store a normalised field (`name_lower`) and query it with an
anchored, case-sensitive `$regex` (`core/queries.md`).

## Partial

```
db.orders.createIndex({created_at: -1}, {name: "pending_by_date", partialFilterExpression: {status: "pending"}})
```

*lab*: `pending_by_date` was 0.6 MB against 64 MB for `_id_`. Used by
`{status: "pending", created_at: {$gte: ...}}` and by `{status: {$in:
["pending"]}, ...}`; COLLSCAN for `{created_at: {$gte: ...}}` alone and
for `{status: "paid", ...}`.

## Unique, and documents without the field

*lab*: with `create_index("email", unique=True)`, a second document with
no email failed: `E11000 duplicate key error collection: lab.u index:
email_1 dup key: { email: null }`. Both of these accepted two documents
without an email and still refused a duplicate address:

```
coll.create_index("email", unique=True, sparse=True)
coll.create_index("email", unique=True, partialFilterExpression={"email": {"$type": "string"}})
```

The partial form also accepted an explicit `email: null`.

## Sparse, and sorting

*lab*: a sparse index on `a` over 101 documents (one without `a`) was not
used for `find({}).sort("a", 1)`: `SORT <- COLLSCAN`, 101 returned. Forced
with `.hint("a_1")` it returned **100**: the document without `a` was
silently missing. Do not hint a sparse or partial index.

## TTL

```
db.sessions.createIndex({expires_at: 1}, {expireAfterSeconds: 0})
```

*lab*: `ttlMonitorSleepSecs` is 60; a document with `expires_at` in the
past was deleted within a minute (`serverStatus().metrics.ttl.
deletedDocuments` went to 1); a document whose `expires_at` was the
string `"not a date"` stayed. `expireAfterSeconds: 0` means "at the time
in the field".

## Text

```
db.products.createIndex({title: "text"})
db.products.find({$text: {$search: "shoe"}})
```

*lab*: matched "Red shoe polish" and "Blue running shoes" (stemmed);
plan `TEXT_MATCH <- FETCH <- IXSCAN(title_text)`. A second text index on
the same collection failed with code 85: `An equivalent index already
exists with a different name and options`. Atlas Search is out of scope.

## Never

- Never promise a collation index helps a `$regex`.
- Never hint a sparse or partial index to force it: results go missing.
- Never add `unique` to an existing field without checking for
  duplicates first (a `$group` by the field with `count > 1`). *lab*:
  `DuplicateKey | Index build failed: ... E11000 duplicate key error`.
