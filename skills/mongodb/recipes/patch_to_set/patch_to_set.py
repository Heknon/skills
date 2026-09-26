"""Write a validated PATCH as a dotted $set, guarded by a revision.

Step 4 of the team's PATCH flow (roadmap R4). Steps 1 and 3 are the
pydantic skill's (`recipes/patch/src/app/patching.py`): they return
`Patched(model, changes)`, where `changes` is a nested dict of the paths
the body set, with validated values. This module turns that into one
update that touches only those paths:

    stored = Customer.model_validate(doc)             # read, with its rev
    result = apply_patch(stored, CustomerPatch, body)  # pydantic skill
    ok = write_patch(coll, doc["_id"], doc["rev"],
                     patch_to_set(stored, result.model, result.changes))
    if not ok: conflict -> 409 or retry (api skill)

Rules (mongodb skill, core/patch-to-set.md):
- A nested model that exists in the stored document is written field by
  field ("address.city"), so its other fields survive.
- A nested model that is stored as null (or missing) is written whole:
  the server refuses a dotted path into null.
- Lists and dict-typed fields are written whole, with the value from the
  validated model (for a dict, pydantic's merge result).
- None is written as null ($set), never $unset.
- A path whose value did not change is left out.
"""

from typing import Any

from pydantic import BaseModel


def patch_to_set(
    before: BaseModel, after: BaseModel, changes: dict[str, Any], *, by_alias: bool = False
) -> dict[str, Any]:
    """The $set document for `changes`: dotted paths to stored values."""
    out: dict[str, Any] = {}
    _walk(before, after, after.model_dump(by_alias=by_alias),
          before.model_dump(by_alias=by_alias), changes, "", out, by_alias)
    return out


def _walk(before: BaseModel, after: BaseModel, new: dict, old: dict,
          changes: dict[str, Any], prefix: str, out: dict[str, Any], by_alias: bool) -> None:
    fields = type(after).model_fields
    for name, sent in changes.items():
        info = fields[name]
        key = (info.alias or name) if by_alias else name
        was, now = getattr(before, name, None), getattr(after, name)
        if (isinstance(sent, dict) and isinstance(was, BaseModel)
                and isinstance(now, BaseModel) and type(was) is type(now)):
            _walk(was, now, new[key], old[key], sent, f"{prefix}{key}.", out, by_alias)
        elif new[key] != old.get(key):
            out[f"{prefix}{key}"] = new[key]


def write_patch(coll, _id: Any, rev: int, set_doc: dict[str, Any], rev_field: str = "rev") -> bool:
    """Apply `set_doc` if the stored revision is still `rev`. False means
    a conflict: another writer changed the document, or it is gone."""
    if not set_doc:
        return coll.count_documents({"_id": _id, rev_field: rev}, limit=1) == 1
    result = coll.update_one({"_id": _id, rev_field: rev},
                             {"$set": set_doc, "$inc": {rev_field: 1}})
    return result.matched_count == 1
