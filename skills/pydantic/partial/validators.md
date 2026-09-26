# Validators and constraints on partial models

The partial model is a subclass that re-declares the required fields.
That has three consequences, confirmed in the lab on pydantic-partial
0.11.1 with pydantic 2.13.5, and on every release from 0.5.2
(`reference/versions.md`).

## 1. Constraints on required fields are dropped

```
UserPatch.model_fields["name"]: Optional[str], metadata []
User.model_fields["name"]:      metadata [MinLen(min_length=3), MaxLen(max_length=40)]
```

*lab:* dropped on required fields: `min_length`, `max_length`, `gt`,
`pattern` (also through `StringConstraints` and `Annotated`). Kept on
fields with a default, which are not re-declared (`d: Annotated[int,
Field(le=10)] = 5` kept `Le(le=10)`). Cause, in `utils.py`
`copy_field_info`: the field is rebuilt with `pydantic.Field(...)` from
its arguments, and `metadata`, where the constraints live, is excluded
(0.10.2 and later) or passed as an unknown keyword that pydantic drops
with a warning (earlier).

So `UserPatch.model_validate({"name": "Al"})` passes. **Fix:** validate
the merged result with the full model (`partial/handoff.md`). Do not
copy the constraints into a hand-written patch model: the two copies
drift.

## 2. Field validators receive `None`

The full model's validators are inherited. For a field sent as `null`
the partial calls them with `None`:

```
PATCH {"name": null}  ->  AttributeError: 'NoneType' object has no attribute 'strip'
```

An `AttributeError` is not a `ValidationError`, so it is a 500 (*lab*).
A validator does not run for a field the body leaves out (defaults are
not validated). **Fix:** make the validator return `None` unchanged.
The full model never passes it `None` for a `str` field, so its
behaviour there is the same, and the merged validation then rejects the
`null` with `string_type`:

```python
@field_validator("name")
@classmethod
def tidy_name(cls, v: str | None) -> str | None:
    if v is None:          # only the partial passes None here
        return v
    return " ".join(v.split()).title()
```

Never delete the validator to make PATCH work: create and PUT lose it
too.

## 3. Model validators see the partial's defaults, not the stored values

A `model_validator(mode="after")` runs on the partial instance, where
unsent fields hold `None` or their defaults. *lab:* stored
`max_items=20`, PATCH `{"min_items": 15}`: the partial compared 15 with
its default `max_items=10` and rejected a valid change; with both
fields required it crashed on `None` (`TypeError: '>' not supported
between instances of 'datetime.date' and 'NoneType'`).

**Fix:** mark the partial parse with a validation context and return
early there; the merged validation runs the rule on real values:

```python
@model_validator(mode="after")
def min_not_above_max(self, info: ValidationInfo) -> "User":
    if info.context and info.context.get("partial"):
        return self                     # checked on the merged result
    if self.min_items > self.max_items:
        raise ValueError("min_items must not be above max_items")
    return self

patch = UserPatch.model_validate(body, context={"partial": True})
```

*lab:* then `{"min_items": 15}` was accepted and `{"min_items": 25}`
rejected with `value_error` at `()`.

## And: validators run again on stored values

The merged result holds the stored values too, and the full model
validates all of them. A validator that is not idempotent corrupts
them: *lab:* a validator hashing `password` turned the stored hash
`30c952fab122` into `083efd83064c` on a PATCH that only changed
`login`. Keep validators idempotent (tidying, checking); do one-way
transformations such as hashing in the service, once, on create or on
a password change.
