# Add or fix a validator

**Verdict you produce:** the validator with its mode named, and the
probe's accepted and rejected inputs.

```
validator: <Class>.<name>, field_validator("<field>", mode="<mode>")
accepts:   <input> -> <value after the validator>
rejects:   <input> -> <type> at <loc>
crashes:   none (each odd input gives a ValidationError)
```

## First: is it a constraint?

Length, range, pattern, `max_digits`: use `Field()` or `Annotated`
(`typing/annotated.md`). They give precise error types
(`string_too_short`, `greater_than`) and appear in the JSON schema. A
validator is for rules a constraint cannot say.

## Choose the mode

| Mode | Receives | Use it to | *lab* (2.13.5) |
| --- | --- | --- | --- |
| `after` (default) | the value, already of the field's type | check or normalise a typed value | `after` on `code: str` with input `42`: `string_type` before the validator runs |
| `before` | the raw input, any type | reshape input before type checking | `v.strip()` on `42` crashed with `AttributeError`, not a `ValidationError` |
| `wrap` | the raw input and a `handler` | run code before and after the core, or skip it | `handler(v) * 10` turned `"3"` into `30`; returning without `handler` skips all checks |
| `plain` | the raw input | replace the core check entirely | `plain` returning `v` put `'abc'` into an `int` field |

The rule of thumb: `after` unless the input must be reshaped first. A
`before` validator must accept every type a client can send:

```python
@field_validator("code", mode="before")
@classmethod
def normalise(cls, v: Any) -> Any:
    if isinstance(v, str):
        return v.strip().upper()
    return v            # not a str: let the type check reject it
```

*lab:* with the guard, `42`, `None` and `["a"]` each gave `string_type`
at `('code',)`. `str(v)` instead accepted them as `'42'`, `'NONE'` and
`"['A']"`.

## What to raise

| Raised in a validator | Becomes | *lab* message |
| --- | --- | --- |
| `ValueError("one is not allowed")` | `value_error` | `Value error, one is not allowed` |
| `assert v != 2, "two fails"` | `assertion_error` | `Assertion failed, two fails` |
| `PydanticCustomError("not_four", "four is {why}", {"why": "bad"})` | your own type `not_four` | `four is bad` |
| `TypeError`, `AttributeError`, anything else | **not caught**: the exception escapes | a crash, a 500 in a web service |

`assert` is removed under `python -O` (*lab:* `n=2` was accepted);
prefer `ValueError`.

## Shapes

```python
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

class Signup(BaseModel):
    password: str
    confirm: str

    @field_validator("confirm")                  # after, on one field
    @classmethod
    def same(cls, v: str, info: ValidationInfo) -> str:
        if v != info.data.get("password"):       # fields validated so far
            raise ValueError("passwords differ")
        return v

    @model_validator(mode="after")               # the whole model
    def check(self) -> "Signup":
        ...
        return self
```

- A field validator is a `@classmethod` that **returns** the value.
- `info.data` holds only fields declared **above** and already valid
  (*lab:* `b` saw `{'a': 1}`, and `{}` when `a` had failed).
- A model validator in `after` mode must return `self`; *lab:*
  returning `None` gave `UserWarning: A custom validator is returning a
  value other than self`, and the error has `loc` `()`.
- `model_validator(mode="before")` is a `@classmethod` receiving the raw
  input (a dict, or anything): check its type first.
- One validator can cover several fields: `field_validator("a", "b")`.
- Validators run on assignment only with `validate_assignment=True`
  (*lab:* without it `a.n = -5` was kept).
- Defaults are not validated (`validate_default=False`), so a validator
  does not run for an omitted field.

## Validators and PATCH

A model with a partial model (pydantic-partial) passes its validators to
the partial, which calls them with `None` and with its own defaults:
`partial/validators.md`.

## Never

- Never raise `TypeError` for bad input; it escapes validation.
- Never call methods on a `before` validator's input without checking
  its type.
- Never write `@validator` or `@root_validator` in v2 code, even to
  match a neighbour (`core/migrate.md`).
