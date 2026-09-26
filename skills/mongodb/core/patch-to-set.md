# Patch to `$set`

**Verdict you produce:** the update a PATCH sends, and proof that the
fields it did not name survive.

```
read:      <document and its revision: rev <n> | Beanie revision_id>
changes:   <Patched.changes from the pydantic skill, e.g. {"address": {"city": "Lyon"}}>
update:    {"$set": {<dotted paths>}, "$inc": {"rev": 1}} filtered on {_id, rev: <n>}
conflict:  matched 0 -> reported to the api skill (409 or retry)
checked:   <test: other fields survive; a stale revision is refused>
```

## The flow and who owns each step

The team's PATCH flow (roadmap R4). The pydantic skill's
`partial/handoff.md` has steps 1 and 3; the api skill decides what
omitted and `null` mean and which status a conflict gets.

| Step | What | Owner |
| --- | --- | --- |
| 1 | parse the body with the partial model | pydantic |
| 2 | read the stored document **with its revision** | mongodb (this file) |
| 3 | merge and validate with the full model; returns `Patched(model, changes)` | pydantic |
| 4 | write only the changed paths as a dotted `$set`, filtered on the revision | mongodb (this file) |
| - | 422, 409 or retry, response body | api |

`changes` is a nested dict of the paths the body set, with values taken
from the validated model (pydantic, `recipes/patch/src/app/
patching.py`). It is not yet an update.

## The rules (decision M5)

`recipes/patch_to_set/patch_to_set.py` applies them; its 15 tests ran on
8.0.32 with pydantic 2.13.5, and against pydantic's own `apply_patch`
(pydantic-partial 0.11.1).

| Changed value | Written as | Why (*lab*) |
| --- | --- | --- |
| a field of a nested model that is stored as a document | `{"address.city": "Lyon"}` | `$set: {address: {city: "Lyon"}}` left `address` as `{city: 'Lyon'}`: street and zip gone |
| a nested model stored as `null` or missing | the whole sub-document, `{"billing": {...}}` | `$set: {"address.city": "Lyon"}` on `{address: null}` failed: `Cannot create field 'city' in element {address: null}` |
| a list | the whole list | positions are not identities; a dotted path into an array by name failed: `Cannot create field 'x' in element {tags: [ "a", "b" ]}` |
| a `dict`-typed field | the whole dict, **from the validated model** | pydantic merges dicts key by key but `changes` holds only the sent keys; writing `changes["prefs"]` would drop the others |
| `None` | `$set: {"email": null}` | never `$unset`: the field stays, with null, as the model says |
| a value equal to the stored one | left out | an empty `$set` means no write |
| the revision | `$inc: {"rev": 1}` in the same update, `rev` in the filter | the update and the check are one atomic operation |

Setting a parent and a child path in one update is refused: `Updating
the path 'address.city' would create a conflict at 'address'`. The rules
above never produce both.

## The write

```python
from patch_to_set import patch_to_set, write_patch

doc = coll.find_one({"_id": oid})                       # step 2: read with rev
stored = Customer.model_validate(doc)
result = apply_patch(stored, CustomerPatch, body)        # pydantic skill, steps 1 and 3
set_doc = patch_to_set(stored, result.model, result.changes)
if not write_patch(coll, oid, doc["rev"], set_doc):      # step 4
    raise Conflict(oid)                                  # api skill: 409 or retry
```

`write_patch` sends `update_one({"_id": oid, "rev": n}, {"$set": set_doc,
"$inc": {"rev": 1}})` and returns `matched_count == 1`. *lab*: after
another writer changed the email and bumped `rev`, the stale patch
matched 0 documents and the other writer's email stayed.

Stored names: pass `by_alias=True` when the collection stores field
aliases. Values are written as `model_dump()` gives them; PyMongo cannot
encode every Python type (*lab*: `Decimal` -> `InvalidDocument: cannot
encode object: Decimal('1.10')`; `uuid.UUID` -> `cannot encode native
uuid.UUID with UuidRepresentation.UNSPECIFIED` unless the client has
`uuidRepresentation="standard"`; a plain `Enum` -> `InvalidDocument`; a
`str` enum is fine). Convert those in the model's serialisers (pydantic
skill) or use Beanie, which encodes them.

## In Beanie

With `use_revision = True` in the document's `Settings`, `await
doc.set(set_doc)` sends one `findAndModify` with `revision_id` in the
filter and a new `revision_id` in the `$set`, and raises
`RevisionIdWasChanged` when the stored one differs
(`beanie/writes.md`, `recipes/beanie_app/app/queries.py`).

## Check it

Run the recipe's server tests against a development database
(`MONGODB_URI` set): the other address fields survive, a stale revision
is refused and keeps the other write, null goes in as null, a whole
sub-document goes into a null parent. A test of the store that uses
mongomock proves none of this: *lab*, mongomock accepted the dotted
`$set` into null silently (`modified_count` 0, no error).

## Never

- Never `$set` a nested dict from a request body.
- Never write a patch without the revision in the filter.
- Never turn `None` into `$unset`, or drop `None` values from the
  update.
