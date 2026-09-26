# PATCH with a partial model, merged and validated again

The pydantic part of the team's PATCH flow (roadmap R4,
`partial/handoff.md`): parse the body with a partial model, merge what
it set onto the stored data, validate the result with the full model,
and hand on the validated model and the changes.

| File | What it is |
| --- | --- |
| `src/app/models.py` | `Address` and `User` (both with `PartialModelMixin`, `extra="forbid"`, constraints, a `None`-safe field validator, a model validator that skips the partial parse) and `UserPatch` |
| `src/app/patching.py` | `apply_patch(stored, patch_model, body) -> Patched(model, changes)`, `deep_merge`, `pick` |
| `tests/test_patching.py` | eleven cases: omitted, `null`, constraints, validator output, nested, a defaulted nested field, lists, a rule across fields, a misspelt key, an empty body |
| `pyproject.toml` | a uv project to run the tests (pydantic 2.12+, pydantic-partial 0.9+) |

## Use it

1. Copy `patching.py` unchanged into the service's schema or service
   layer (where it goes: the architecture skill).
2. For each model with a partial, apply the four rules at the top of
   `models.py`: the mixin on every nested model, `"<field>.*"` for
   nested fields with defaults, field validators that accept `None`,
   model validators that return early when `info.context` has
   `"partial"`.
3. In the endpoint: `result = apply_patch(stored, UserPatch, body)`,
   then store `result.changes` and return `result.model`. A
   `ValidationError` from `apply_patch` is a 422 (api skill); writing
   `changes` as a dotted `$set` is the mongodb skill's.
4. On pydantic 2.11, drop `exclude_computed_fields=True` (2.12+), and
   on a model with computed fields dump with `exclude={...}` naming
   them. On 2.10, also drop `by_name=True` (2.11+) and set
   `populate_by_name=True` on models with aliases. *lab:* with those
   arguments removed, the tests passed on 2.11.10 and 2.10.6 (the
   recipe's models have no aliases or computed fields).

## Run it (PowerShell or POSIX)

```
cd recipes/patch
uv sync
uv run pytest                          # 11 passed
```

*lab:* 11 passed with pydantic 2.13.5 and pydantic-partial 0.11.1,
0.10.2 and 0.9.0 (0.9.0 adds four `metadata` warnings), and with
pydantic 2.12.5 and 0.11.1. The tests can fail: with the naive
`model_copy(update=patch.model_dump())`, 9 failed; without the
`context` flag, 1 failed (the rule across fields); with
`exclude_unset=True` but `model_copy` instead of validating again, 5
failed.
