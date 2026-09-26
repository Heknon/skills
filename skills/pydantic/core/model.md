# Write or change a model

**Verdict you produce:** the model, and a probe that shows it accepts
what it must and rejects what it must.

```
model:    <path>::<Class>, pydantic <version>
accepts:  <input> -> <result>          (one line per case, from the probe)
rejects:  <input> -> <type> at <loc>
```

## Steps

1. **Read the versions** (`uv pip show pydantic`) and the models next
   to yours. Copy their v2 conventions (`model_config = ConfigDict(...)`,
   `field_validator`); never copy a v1 one (`class Config`,
   `@validator`): `core/migrate.md` says how to spot them.
2. **Decide each field's shape** with the table below and
   `typing/required-and-optional.md`.
3. **Put limits in constraints, not validators**: `Field(min_length=3)`,
   `Field(gt=0)`, `Field(pattern=...)`, or a reusable `Annotated` type
   (`typing/annotated.md`). A validator is for what a constraint cannot
   say (`core/validate.md`).
4. **Set only the config you need** (`reference/config.md` has every key
   and its default).
5. **Probe it** (`core/probe.md`) with the valid cases, the invalid ones,
   and the edges: missing, `null`, wrong type, an extra key.

## Field shapes

| The field must | Write |
| --- | --- |
| always be sent, never `null` | `name: str` |
| always be sent, `null` allowed | `referrer: str \| None` (no default) |
| be optional to send, never `null` | `status: str = "active"` |
| be optional to send, `null` allowed | `nickname: str \| None = None` |
| start as a new list or dict each time | `tags: list[str] = []` (*lab:* not shared between instances) or `Field(default_factory=list)` |
| be computed from other fields | `@computed_field` on a `@property` (`core/serialize.md`) |
| never change after creation | `Field(frozen=True)` (*lab:* `frozen_field` on assignment) |

A default is not validated unless `validate_default=True`: *lab:*
`n: int = Field(default="x")` built `Fac(n='x')` with no error.

## Config that changes behaviour

| Need | `model_config = ConfigDict(...)` | *lab* (2.13.5) |
| --- | --- | --- |
| reject unknown keys | `extra="forbid"` | `extra_forbidden` at `('b',)`; the default `ignore` drops them silently |
| keep unknown keys | `extra="allow"` | kept in the dump and in `model_extra` |
| immutable and hashable | `frozen=True` | assignment gives `frozen_instance`; equal models hash equal |
| check assignments | `validate_assignment=True` | `v.a = "x"` gives `int_parsing`; without it, anything is assigned |
| read from objects (ORM rows, dataclasses) | `from_attributes=True` | without it: `model_type` |
| strip or limit every `str` | `str_strip_whitespace=True`, `str_max_length=` | strip runs before the length check |
| accept field names where aliases exist | `validate_by_name=True` (2.11+), older `populate_by_name=True` | `core/serialize.md` |

## Traps

- `model_construct(**data)` skips validation entirely (*lab:*
  `a='not int'` accepted). Use it only for data already validated.
- `model_copy(update={...})` does not validate either (*lab:*
  `c='not an int'` accepted). To change fields and check them, dump,
  change, and `model_validate` again.
- A field named `model_...` is allowed; only the prefixes
  `model_validate` and `model_dump` are protected in 2.13.5
  (`reference/config.md`).
- Settings classes are models too, but read their values from sources:
  `settings/sources.md`.

## Never

- Never make a field `Optional` to silence a checker or to let a test
  pass; that changes what the model accepts.
- Never loosen `extra="forbid"` to make one input pass without asking:
  the forbid is often the only thing catching misspelt keys.
