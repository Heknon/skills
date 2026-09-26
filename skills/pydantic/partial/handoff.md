# PATCH and PUT: pydantic's part, and what it hands on

**Verdict you produce** for a PATCH or PUT body task:

```
pydantic-partial: <version>        (partial/check-installed.md)
body model:       <UserPatch = ...>, or the full model for PUT
validated:        body with the partial; merged result with <Full model>
hands on:         model (validated) and changes (nested dict of what the body set)
checked:          <each case: omitted, null, invalid, nested, constraint> -> <result>
```

## The flow, and who owns each step

The team's agreed flow for a PATCH (roadmap decision R4):

| Step | What | Owner |
| --- | --- | --- |
| 1 | parse the body with the partial model | pydantic (this file) |
| 2 | read the stored document and its revision | mongodb |
| 3 | merge the body onto the stored data and validate the result with the **full** model | pydantic (this file) |
| 4 | write only the changed fields as a dotted `$set`, filtered on the revision; lists replaced whole; `null` is `$set: null`, never `$unset` | mongodb |
| - | what omitted and `null` mean, the status codes: 422 for a `ValidationError`, 409 (or a retry) for a revision mismatch | api |

Step 3 is not optional. The partial model cannot enforce the full
model's rules: it drops constraints, feeds validators `None`, runs model
validators on defaults (`partial/validators.md`), and knows nothing of
the stored values that rules across fields need. `model_copy(update=...)`
validates nothing (*lab:* it accepted `'not an int'` for an `int`).

## Steps 1 and 3 in code

From `recipes/patch/src/app/patching.py` (ran on pydantic 2.12.5 and
2.13.5 with pydantic-partial 0.9.0, 0.10.2 and 0.11.1):

```python
def apply_patch(stored: M, patch_model: type[BaseModel], body: Any) -> Patched[M]:
    patch = patch_model.model_validate(body, context={"partial": True})
    sent = patch.model_dump(exclude_unset=True)
    base = stored.model_dump(exclude_computed_fields=True)   # 2.12+
    merged = deep_merge(base, sent)                          # dicts key by key
    model = type(stored).model_validate(merged, by_name=True)  # 2.11+
    return Patched(model=model, changes=pick(model.model_dump(), sent))
```

- `exclude_unset=True`: only what the body sent (`partial/unset-and-none.md`).
- `deep_merge`: nested dicts merge; lists and everything else replace.
- `exclude_computed_fields=True`: a computed field in the dump would be
  rejected as `extra_forbidden` by a full model with `extra="forbid"`
  (*lab*).
- `by_name=True`: the dump uses field names; with aliases, validating it
  by alias would fail with `missing` (*lab*).
- `changes` takes each sent path's value **from the validated model**,
  because a validator may change it: *lab:* body `"  Bea   Stone "`,
  `changes == {"name": "Bea Stone"}`. Writing the raw body would store
  what validation rejected or rewrote.

## What pydantic hands on

`Patched.model`, the full validated model, for the response; and
`Patched.changes`, a nested dict with only the paths the body set, for
the store. Turning `{"address": {"city": "Lyon"}}` into
`{"$set": {"address.city": "Lyon"}}` guarded by the revision is the
mongodb skill's ground (`skills/mongodb/core/patch-to-set.md`); what
the endpoint returns and which status it uses is the api skill's
(`skills/api/core/put-and-patch.md`).

**A `dict`-typed field.** `deep_merge` merges a dict key by key, but
`changes` holds only the keys the body sent. *lab* (pydantic 2.13.5,
pydantic-partial 0.11.1): stored `prefs={"lang": "fr", "theme":
"dark"}`, body `{"prefs": {"theme": "light"}}` gave `model.prefs ==
{"lang": "fr", "theme": "light"}` but `changes == {"prefs": {"theme":
"light"}}`. Writing `changes["prefs"]` as the new value drops `lang`.
The store writes a dict field whole, from the validated `model`, as
mongodb's `recipes/patch_to_set/` does (it produced `{"prefs": {"lang":
"fr", "theme": "light"}}` for this body).

## The partial model is not the endpoint's body parameter

FastAPI validates a body parameter with no validation context. *lab*
(FastAPI 0.141.1): a model validator on the body model saw
`info.context` as `None`. So the early return on `context={"partial":
True}` (`partial/validators.md`) never happens, and an inherited model
validator runs on the partial's defaults. Declare the body as a `dict`,
call `apply_patch` inside the endpoint, and turn its `ValidationError`
into a 422: the api skill's procedure, in
`skills/api/core/put-and-patch.md`.

## PUT

A PUT replaces the resource: validate the body with the **full** model
(`User.model_validate(body)`); no partial, no merge. Omitted fields take
their defaults. Whether the API offers PUT, PATCH or both is api's
decision.

## Checked cases (the recipe's tests, *lab*)

| Body | Result |
| --- | --- |
| `{"name": "Bea Stone"}` | name changed; email and status kept, not reset |
| `{"email": null}` | email cleared |
| `{"name": null}` | `string_type` at `('name',)` |
| `{"name": "Al"}` | the partial accepts it; the merge rejects it: `string_too_short` |
| `{"address": {"city": "Lyon"}}` | city changed, street kept |
| `{"billing": {"postcode": "69001"}}` (a defaulted nested field) | accepted, via `"billing.*"` |
| `{"tags": ["c"]}` | list replaced whole |
| `{"min_items": 15}` with stored `max_items=20` | accepted; `25` gives `value_error` at `()` |
| `{"nmae": "Bea"}` | `extra_forbidden` (the model has `extra="forbid"`) |
| `{}` | nothing changes, `changes == {}` |

The naive version (`model_copy(update=patch.model_dump())`) failed 9 of
these 11 tests; without the `context` flag, 1 failed; with
`exclude_unset` but `model_copy`, 5 failed (*lab*).
