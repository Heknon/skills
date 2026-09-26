# Indexes in Beanie

Beanie 2.2.0, MongoDB 8.0.32, *lab*. Which indexes to have is
`core/index-design.md`; how to build them on a live collection is
`core/index-live.md`. This file is how Beanie declares and sends them.

## Declaring

| Form | Declares |
| --- | --- |
| `email: Indexed(str)` | `{email: 1}`, name `email_1` |
| `email: Indexed(str, unique=True)` | `{email: 1}` unique (*lab*: `{"unique": true, "name": "email_1", "key": {"email": 1}}`) |
| `Settings.indexes = [IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="status_1_created_at_-1")]` | a compound index, with any `IndexModel` option (`partialFilterExpression`, `collation`, `expireAfterSeconds`) |

Compound indexes, partial indexes and collations need `Settings.indexes`
with PyMongo's `IndexModel`; `Indexed` is one field. Name every index
explicitly: the name is what `$indexStats`, hints and drops use.

## What `init_beanie` does with them

At every start, unless `skip_indexes=True`:

1. `listIndexes` on the collection (*lab*: `NamespaceNotFound` on a
   collection that does not exist yet; Beanie carries on).
2. `createIndexes` with **all** declared indexes. For indexes that exist
   with the same options the server does nothing (*lab*: `note: 'all
   indexes already exist'`, 0.00 s). For a new one it **builds it and
   the call waits** (*lab*: 1.4 s for `total_cents` on 1,000,000
   small documents; on production, time a build on a copy rather than
   scale this number).
3. With `allow_index_dropping=True`, first `dropIndexes` for each
   existing index the models do not declare, including indexes made by
   hand (*lab*: `price_by_ops` dropped).

Two failures at this step stop the application from starting (*lab*):

| Server state | `init_beanie` raises |
| --- | --- |
| the declared index exists but is hidden | `OperationFailure: An equivalent index already exists with the same name but different options ... hidden: true`, code 85 `IndexOptionsConflict` |
| the model adds `unique=True` to an index that exists without it, same name | code 86 `IndexKeySpecsConflict`: `An existing index has the same name as the requested index.` Change it with a planned build under a new name, then drop the old one |

## The rules for a service

1. The models declare every index the code needs: they are the record.
2. The service starts with `skip_indexes=True`.
3. A separate step builds them: `recipes/beanie_app/build_indexes.py`
   (calls `init_beanie` with index creation on), run as a one-off job
   before the release (deployment skill), or the `createIndexes` command
   by a person (`core/index-live.md`).
4. Tests and development may build at startup.
5. `allow_index_dropping` stays off.
