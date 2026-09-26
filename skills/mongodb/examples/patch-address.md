# Worked example: a PATCH that wiped an address

Kinds: Write, with the pydantic skill for the body. MongoDB 8.0.32,
PyMongo 4.18.2, pydantic 2.13.5.

## The ask

> PATCH /customers/{id} with `{"address": {"city": "Lyon"}}` loses the
> street and zip code. Fix `save_patch` in store.py.

```python
def save_patch(coll, customer_id, changes):
    coll.update_one({"_id": customer_id}, {"$set": changes})
```

`changes` comes from the pydantic skill's `apply_patch`: the nested dict
of what the body set, `{"address": {"city": "Lyon"}}`.

## Steps

1. **Reproduce** on the development server (mongosh):
   ```
   db.lab.insertOne({_id: 1, address: {street: "1 Main St", city: "Paris", zip: "75001"}, rev: 1})
   db.lab.updateOne({_id: 1}, {$set: {address: {city: "Lyon"}}})
   db.lab.findOne({_id: 1})      // { _id: 1, address: { city: 'Lyon' }, rev: 1 }
   ```
   `$set` of a sub-document replaces it whole.
2. **The rule** (`core/patch-to-set.md`): changed paths of a stored
   nested model are dotted; lists and dicts whole; `None` as null; a
   revision in the filter.
   ```
   db.lab.updateOne({_id: 1}, {$set: {"address.city": "Lyon"}})
   // { _id: 1, address: { street: '1 Main St', city: 'Lyon', zip: '75001' }, rev: 1 }
   ```
3. **Change the code**: copy `recipes/patch_to_set/patch_to_set.py` next
   to `store.py`, and read the revision with the document:
   ```python
   def save_patch(coll, customer_id, stored, rev, result) -> None:
       set_doc = patch_to_set(stored, result.model, result.changes)
       if not write_patch(coll, customer_id, rev, set_doc):
           raise Conflict(customer_id)          # the api skill maps it: 409 or retry
   ```
   `Customer` gains `rev: int = 1`; existing documents without `rev`
   need it set once (`update_many({"rev": {"$exists": false}}, {"$set":
   {"rev": 1}})`, asked for as part of the change).
4. **Edge found by the tests**: a customer whose `billing` is stored as
   `null`, patched with `{"billing": {"city": "Nice", ...}}`. A dotted
   path fails on the server: `Cannot create field 'city' in element
   {billing: null}`. `patch_to_set` writes the whole sub-document when
   the stored value is not a document.
5. **Tests against the server** (`MONGODB_URI` set): `uv run pytest` in
   the recipe: `15 passed`. The test that matters here:
   `test_other_address_fields_survive`, and
   `test_stale_revision_is_a_conflict_and_keeps_the_other_write`.
6. **Can they fail?** With `patch_to_set` changed to write every changed
   nested model whole, `test_nested_field_becomes_a_dotted_path` failed.

## The answer

```
## Result
save_patch now writes {"$set": {"address.city": "Lyon"}, "$inc": {"rev": 1}}
filtered on {_id, rev}: only the paths the body changed. Lists and dict
fields are replaced whole, None is stored as null, a null parent gets the
whole sub-document. A stale revision matches nothing and raises Conflict
(for the api skill to turn into 409). Parsing and validating the body stay
in the pydantic skill's apply_patch.

## Checked
- 8.0.32, development: the old $set left address = {city: 'Lyon'}; the
  dotted $set kept street and zip.
- recipes/patch_to_set tests: 15 passed with MONGODB_URI; breaking the
  dotted rule made test_nested_field_becomes_a_dotted_path fail.

## Not checked
- Existing documents without rev: the one-off update_many is prepared, not
  run on production.
- The endpoint's status codes: api skill.
```
