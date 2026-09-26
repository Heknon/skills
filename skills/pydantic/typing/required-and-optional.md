# Required, nullable and optional

Two separate questions for every field, answered by two separate parts
of the declaration:

- **May it be left out?** Only if it has a **default**.
- **May it be `null`?** Only if its **type** admits `None`.

`Optional[X]` is `X | None`: it answers the second question, never the
first.

## The four shapes (*lab*, 2.13.5)

```python
class M(BaseModel):
    a: Optional[str]            # required, may be None
    b: Optional[str] = None     # may be left out, may be None
    c: str = "x"                # may be left out, not None
    d: str                      # required, not None
```

| Input | Result |
| --- | --- |
| `{}` | `missing` at `('a',)` (and `('d',)`): `Field required` |
| `{"a": None, "d": "v"}` | `a=None b=None c='x' d='v'`, `model_fields_set == {'a', 'd'}` |
| `{"a": None, "c": None, "d": "v"}` | `string_type` at `('c',)` |

`M.model_fields["a"].is_required()` is `True`; for `b` and `c` it is
`False`.

## Choosing

| The contract says | Write |
| --- | --- |
| clients may omit it | give it a default: `nickname: str \| None = None`, or a real default |
| clients must send it, `null` allowed | `referrer: str \| None` with no default |
| clients must send a value | `name: str` |
| the server fills it when absent | a default or `Field(default_factory=...)` |

A required-nullable field is a deliberate contract ("always send it,
even as null"); do not add `= None` to it to make an error go away.
Check the docstring, the API description or the tests first.

## Defaults and `None`

- `Field(default=None)` and `= None` are the same.
- A default is not validated (`validate_default=False`), so
  `x: int = None` is accepted by pydantic and yields `None` at run time,
  while checkers report the mismatch. Write `int | None = None`.
- A constraint on an optional field applies to the value when one is
  given: *lab:* `x: Optional[str] = Field(None, min_length=2)` rejected
  `"a"` with `string_too_short` and accepted `None`.

## How checkers see it

The same way: *lab:* pyright reported `Argument missing for parameter
"nickname"` and mypy `Missing named argument "nickname" for "Opt"` for
a required `Optional` (`typing/checkers.md`).

## In PATCH bodies

A partial model makes every required field optional with default
`None`; telling "left out" from "sent as null" then needs
`model_fields_set` or `exclude_unset`: `partial/unset-and-none.md`.
