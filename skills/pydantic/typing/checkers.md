# What each checker says about a model

pydantic's `BaseModel` is marked with `dataclass_transform`, so pyright,
basedpyright and mypy build an `__init__` from the annotations: one
keyword parameter per field, named by `alias` when `Field(alias=...)`
is given, required when there is no default. They do not run pydantic,
so they know nothing of lax conversion, `populate_by_name`,
`validate_by_name`, alias generators or settings sources. mypy with the
`pydantic.mypy` plugin knows some of that.

## The shapes (*lab*, pydantic 2.13.5)

```python
class Payment(BaseModel):            # alias, populate_by_name
    model_config = ConfigDict(populate_by_name=True)
    amount_cents: int = Field(alias="amountCents")

class Payment2(BaseModel):           # validation_alias only
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    amount_cents: int = Field(validation_alias="amountCents")

class Gen(BaseModel):                # alias generator
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    amount_cents: int

class Opt(BaseModel):
    nickname: Optional[str]

class Coerce(BaseModel):
    n: int

Payment(amount_cents=5)   # A
Payment(amountCents=5)    # B
Payment2(amount_cents=5)  # C
Gen(amount_cents=5)       # D
Opt()                     # E
Coerce(n="5")             # F
```

| Line | pyright 1.1.414 / basedpyright 1.40.1 | mypy 2.3.1 | mypy + `pydantic.mypy` | + `init_typed`, `init_forbid_extra` |
| --- | --- | --- | --- | --- |
| A by field name | `No parameter named "amount_cents"`, `Argument missing for parameter "amountCents"` | `Unexpected keyword argument "amount_cents" for "Payment"; did you mean "amountCents"?` | ok | ok |
| B by alias | ok | ok | `Missing named argument "amount_cents" for "Payment"` | `Unexpected keyword argument "amountCents"` |
| C `validation_alias` | ok | ok | ok | ok |
| D alias generator | ok (generated aliases are invisible) | ok | ok | ok |
| E Optional, no default | `Argument missing for parameter "nickname"` | `Missing named argument "nickname" for "Opt"` | same | same |
| F `"5"` for `int` | `Argument of type "Literal['5']" cannot be assigned to parameter "n" of type "int"` | `Argument "n" to "Coerce" has incompatible type "str"; expected "int"` | ok | same error as without the plugin |

What the table says:

- `Field(alias=...)` fights one checker or the other depending on the
  call style. `validation_alias` plus `serialization_alias` (line C) is
  quiet everywhere and behaves the same at run time (*lab:* the
  pyright-alias tests passed with it and pyright reported `0 errors`).
- An alias generator hides the aliases from every checker; calls by
  field name are accepted, calls by alias would be flagged.
- A required `Optional` is required for every checker, as for pydantic.
- Lax conversion is invisible to pyright; build models from untyped
  data with `model_validate`, whose argument is typed `Any`.

## Other messages seen in the lab

| Code | Checker, message | Meaning, fix |
| --- | --- | --- |
| `Settings()` with a required field | pyright: `Argument missing for parameter "db_password"`; mypy without plugin: `Missing named argument`; mypy + plugin: ok | the value comes from a source; see `core/checker.md` for the narrow ignore |
| `UserPatch(name="x")` (pydantic-partial) | pyright: `Argument missing for parameter "id"`; mypy + plugin: `Missing named argument "id" for "User"` | the partial is typed as the full model (`reveal_type` shows `User`); use `model_validate` |
| `class UserPatch(User.model_as_partial())` | mypy: `Unsupported dynamic base class "User.model_as_partial"  [misc]` | use `create_model` |
| `model_config = ConfigDict(...)` | basedpyright `recommended` mode only: `Type annotation for attribute model_config is required because this class is not decorated with @final (reportUnannotatedClassAttribute)` | `model_config: ClassVar[ConfigDict] = ConfigDict(...)`; pydantic accepts it (*lab*) and all three checkers are then quiet |
| `Optional[str]` | basedpyright `recommended`: `This type is deprecated as of Python 3.10; use "\| None" instead (reportDeprecated)` | write `str \| None`; same meaning |

The mypy plugin is switched on in the mypy configuration
(`plugins = pydantic.mypy`); where that goes is the linting skill's
ground.
