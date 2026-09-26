# PATCH as a dotted `$set`, guarded by a revision

Step 4 of the PATCH flow (roadmap R4, `core/patch-to-set.md`). Steps 1
and 3 are the pydantic skill's recipe (`recipes/patch/` in that skill),
which returns `Patched(model, changes)`.

| File | What it is |
| --- | --- |
| `patch_to_set.py` | `patch_to_set(before, after, changes, by_alias=False)` -> the `$set` document; `write_patch(coll, _id, rev, set_doc)` -> `True`, or `False` on a conflict |
| `tests/models.py` | `Address`, `Customer` with a list, a dict field, an optional nested model, an alias and a validator |
| `tests/test_patch_to_set.py` | nine rules, no server |
| `tests/test_on_server.py` | six cases against a development server: fields survive, the naive `$set` wipes them, a stale revision is refused, null parents, `None` stored as null |

## Use it

1. Copy `patch_to_set.py` next to the repository code (where it goes:
   the architecture skill).
2. Keep a revision in each document (`rev`, an integer from 1), read it
   with the document, and pass it to `write_patch`.
3. `False` from `write_patch` is a conflict: the api skill maps it to
   409 or a retry.

*lab*: with `MONGODB_URI` set, 15 passed (pydantic 2.13.5, PyMongo
4.18.2, MongoDB 8.0.32); without it, 9 passed and 6 skipped. The tests
can fail: never recursing into nested models failed 1; taking values
from `changes` instead of the model failed 2; recursing into `dict`
fields failed 3. Fed with the pydantic skill's `apply_patch` (pydantic-
partial 0.11.1), it produced `{'address.city': 'Lyon'}`, `{'email':
None}`, `{'tags': ['c']}`, `{'name': 'Bea Stone'}` for the bodies of
that recipe's tests.
