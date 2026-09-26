# Writes in Beanie, and what they send

Beanie 2.2.0, PyMongo 4.18.2, MongoDB 8.0.32. Commands recorded with
PyMongo command monitoring (*lab*); the method bodies read in
`beanie/odm/documents.py`.

## Calls and commands

| Beanie | Command sent |
| --- | --- |
| `await doc.insert()` | `insert` of the document |
| `await Model.insert_many(docs)` | one `insert` (*lab*: 1,000 documents, one command) |
| `await doc.save()` | `findAndModify` on `_id`, `$set` of **every field**, `upsert: true` |
| `await doc.set({Model.field: v})` or `doc.set({"address.city": v})` | `findAndModify` on `_id`, `$set` of those paths only, `upsert: false` |
| `await doc.inc({Model.points: 7})` | `findAndModify`, `$inc` |
| `await doc.save_changes()` (needs `use_state_management`) | `findAndModify`, `$set` of the changed paths, dotted (*lab*: `{"address.city": "Lyon"}`) |
| `await doc.replace()` | a replace of the whole document |
| `await Model.find(q).update({...})` | one `update` with `multi: true` |
| `BulkWriter` around `set`/`insert_one` calls | one `update` or `insert` with all of them at exit |

With `use_revision = True`, every one of these that goes through
`update()` adds `revision_id` to the filter and a new `revision_id` to
the `$set`.

## `save()` on a stale copy loses other writes

*lab*: request A and request B read the same customer; B changed the
email and saved; A, holding its older copy, changed the name and saved.
The stored document had A's name and the **old** email: `save()` sent
`$set` of every field, including the email A had read. The same happened
with the nightly job pattern "get, call a slow service, set one field,
`save()`" while support changed an email: the email reverted.

Fixes, in order of preference:

1. **Send only what changed**: `await customer.set({Customer.
   loyalty_points: points})`, or `inc` for counters. *lab*: the email
   change survived.
2. **Refuse stale writes**: `use_revision = True` in `Settings`. *lab*:
   the stale `set` sent `{"_id": ..., "revision_id": <old>}` as its
   filter, matched nothing, and raised `RevisionIdWasChanged`; the stale
   `save()` (an upsert) hit `E11000 duplicate key error ... _id_`, which
   Beanie also turned into `RevisionIdWasChanged`. The caller decides:
   reload and retry, or report a conflict (api skill: 409).
3. **State management**: `use_state_management = True` and
   `save_changes()` send only the paths changed since the load. It still
   writes those paths over any concurrent change to the same paths; add
   the revision when that matters.

A transaction does not fix a lost update between two requests; it only
groups writes inside one.

## A PATCH in Beanie

The PATCH flow is `core/patch-to-set.md`. With `use_revision = True`:

```python
set_doc = patch_to_set(stored, result.model, result.changes)   # recipes/patch_to_set
try:
    await customer.set(set_doc)          # one findAndModify, filtered on revision_id
except RevisionIdWasChanged:
    raise Conflict(customer.id)
```

*lab*, `recipes/beanie_app` test: the command was `findAndModify` with
`revision_id` in `query` and exactly `{"address.city", "revision_id"}`
in `$set`; the street and zip survived; a second, stale patch raised the
conflict and the first writer's email stayed.

## Bulk

```python
async with BulkWriter(ordered=False) as bw:
    for item in items:
        await item.set({Item.qty: item.qty + 1}, bulk_writer=bw)
```

*lab*: 100 `set` calls became one `update` command with 100 entries,
`ordered: false`. All operations in one `BulkWriter` must target one
collection (`ValueError: All the operations should be for a same
collection name`). Errors are PyMongo's `BulkWriteError`
(`pymongo/bulk.md`).
