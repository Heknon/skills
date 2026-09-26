# Worked example: the PATCH that reset fields

Kinds: Update, Endpoint, Test. Outputs from a lab run on FastAPI
0.141.1, Starlette 1.7.0, pydantic 2.13.5 (the eval sandbox
patch-resets).

## The ask

> Clients need to set a nickname on their profile. Add an optional
> nickname (at most 20 characters) and let PATCH /profiles/{id} change
> it, the same way the other fields are handled.

The existing endpoint:

```python
@app.patch("/profiles/{profile_id}")
def update_profile(profile_id: int, body: ProfileUpdate) -> Profile:
    ...
    stored = PROFILES[profile_id]
    PROFILES[profile_id] = stored.model_copy(update=body.model_dump())
    return PROFILES[profile_id]
```

## Steps

1. **Try "the same way" before copying it.** A probe that sends one
   field at a time (`probe_patch.py`, run with
   `$env:PYTHONPATH = "src"; uv run --no-sync python probe_patch.py`):
   ```
   {'bio': 'Runner'} -> 200 {'id': 1, 'display_name': None, 'bio': 'Runner'}
   {'display_name': None} -> 200 {'id': 1, 'display_name': None, 'bio': None}
   ```
   Sending only `bio` erased `display_name`; `display_name: null` was
   accepted although the model says `min_length=1`. The existing test
   passes because it sends every field.
2. **Name the cause** (`core/put-and-patch.md`). A PATCH is a merge
   patch: omitted stays, `null` clears. `body.model_dump()` sends every
   field of `ProfileUpdate`, the unsent ones as `None`
   (`skills/pydantic/partial/unset-and-none.md`), and `model_copy`
   validates nothing; FastAPI did not catch it on the way out because
   the returned object is a `Profile` instance
   (`fastapi/responses.md`).
3. **Fix the endpoint, then add the field.** Dump with
   `exclude_unset=True`, merge onto the stored profile, validate the
   result with the full `Profile`, and turn a `ValidationError` raised
   here into the usual 422 (a 500 otherwise):
   ```python
   sent = body.model_dump(exclude_unset=True)
   try:
       updated = Profile.model_validate({**stored.model_dump(), **sent})
   except ValidationError as e:
       raise RequestValidationError(
           [{**err, "loc": ("body", *err["loc"])} for err in e.errors(include_url=False)]
       ) from e
   ```
   `nickname: str | None = Field(default=None, max_length=20)` goes on
   `Profile`, and `nickname: str | None = None` on `ProfileUpdate`,
   which also gets `extra="forbid"` so a misspelt key is a 422 instead
   of a PATCH that silently does nothing. The limit lives only on
   `Profile`; the merged validation enforces it. The body model has no
   model validators, so FastAPI validating it without a partial context
   is harmless here (`core/put-and-patch.md`).
4. **Tests**, with a fixture that resets the stored profile and uses
   `with TestClient(app)`: nickname alone keeps the rest, `null` clears
   the nickname, `null` display name is 422 at `['body',
   'display_name']`, 21 characters is 422 `string_too_long`.
   `uv run pytest -q`: `5 passed in 0.32s`.
5. **The probe again**:
   ```
   {'bio': 'Runner'} -> 200 {'id': 1, 'display_name': 'Ann', 'bio': 'Runner', 'nickname': None}
   {'display_name': None} -> 422 {'detail': [{'type': 'string_type', 'loc': ['body', 'display_name'], 'msg': 'Input should be a valid string', 'input': None}]}
   ```
6. **Can the tests fail?** Put `body.model_dump()` back:
   `3 failed, 2 passed` (the nickname, null and length tests). Restored:
   `5 passed`.
7. **The contract**: `app.openapi()` shows the body as
   `$ref ProfileUpdate` with `nickname` as `anyOf string, null`: an
   optional request field, an additive change (`core/compatibility.md`
   rule 2).

## The answer

```
## Result
PATCH /profiles/{id} reset every field the body left out: it dumped
the body with model_dump() and merged with model_copy, which validates
nothing, so {"bio": "Runner"} erased display_name with a 200. Fixed in
src/profiles/main.py: exclude_unset=True, merge onto the stored
profile, validate with Profile, and a ValidationError becomes a 422.
Added nickname (optional, max 20, on Profile; ProfileUpdate now rejects
unknown keys). Omitted fields stay, null clears nickname, null
display_name is a 422.

## Checked
- probe before: {'bio': 'Runner'} -> 200 with display_name None.
- uv run pytest -q: 5 passed; with model_dump() put back, 3 failed.
- probe after: display_name kept; {'display_name': null} -> 422.
- FastAPI 0.141.1, Starlette 1.7.0, pydantic 2.13.5.

## Not checked
- Clients that relied on the reset (sending one field to clear the
  others): none known; that behaviour was a bug, but it was observable.
- Concurrent PATCHes (no revision in this store): see core/put-and-patch.md, Races.
```
