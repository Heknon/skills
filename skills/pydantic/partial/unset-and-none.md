# Unset against `None`

A PATCH body can say three different things about a field:

| Body | Means (the api skill's contract) | In the partial instance |
| --- | --- | --- |
| field absent | leave it unchanged | value `None` or the field's default; **not** in `model_fields_set` |
| `"email": null` | clear it | value `None`; in `model_fields_set` |
| `"email": "a@b.c"` | set it | the value; in `model_fields_set` |

Only `model_fields_set` tells the first two apart, and
`model_dump(exclude_unset=True)` is built on it.

*lab (0.11.1, 2.13.5)*, `User` with `id: int`, `name: str`,
`email: str | None = None`, `status = "active"`:

```
UserPatch.model_validate({"name": "Xavier"}).model_dump()
    {'id': None, 'name': 'Xavier', 'email': None, 'status': 'active'}
UserPatch.model_validate({"name": "Xavier"}).model_dump(exclude_unset=True)
    {'name': 'Xavier'}
UserPatch.model_validate({"email": None}).model_fields_set
    {'email'}
```

## Each dump merged onto a stored user

The stored user has `email='ann@example.com'` and `status='suspended'`.

| Dump of the patch | `{"name": "Xavier"}` | `{"email": null}` | `{"status": "active"}` |
| --- | --- | --- | --- |
| `model_dump()` | all fields: **`id`, `email` set to `None`, `status` to `'active'`** | same resets | same resets |
| `model_dump(exclude_none=True)` | `{'name': 'Xavier', 'status': 'active'}`: status reset | `{'status': 'active'}`: **email not cleared**, status reset | `{'status': 'active'}` |
| `model_dump(exclude_defaults=True)` | `{'name': 'Xavier'}` | `{}`: **email not cleared** (`None` is its default) | `{}`: **cannot set a field back to its default** |
| `model_dump(exclude_unset=True)` | `{'name': 'Xavier'}` | `{'email': None}` | `{'status': 'active'}` |

(*lab*, every cell; merged, the first row gave `id=None name='Xavier'
email=None status='active'`.) Use `exclude_unset=True`, and only that.

## Nested and lists

`exclude_unset` applies at every level: *lab:* `{"address": {"city":
"Lyon"}}` dumped as `{'address': {'city': 'Lyon'}}`. So the merge onto
the stored data must be **deep** for dicts: a plain `dict.update`
replaces the whole `address` with `{'city': 'Lyon'}` and the full model
then fails with `missing` at `('address', 'street')` (*lab*). A list is
a value: the body's list replaces the stored one whole.

## `null` on a field that cannot be `None`

The partial accepts `{"name": null}` (its `name` is `Optional`). The
full model rejects the merged result with `string_type` at `('name',)`
(*lab*), which the web layer turns into a 422 (api skill). That check
is only there if the merged result is validated: `partial/handoff.md`.
