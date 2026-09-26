# Worked example: a v1 model migrated to v2

Kinds: Migrate, Validate. Outputs from a lab run on pydantic 2.13.5,
Python 3.12.

## The ask

> Our tests print warnings about V1 validators. Move billing/invoice.py
> to pydantic v2 without changing what it does.

```python
class Invoice(BaseModel):
    number: str
    currency: str
    issued: date
    due: date

    class Config:
        orm_mode = True

    @validator("currency", pre=True)
    def upper_currency(cls, v):
        return v.upper()

    @root_validator(skip_on_failure=True)
    def due_after_issued(cls, values):
        if values["due"] < values["issued"]:
            raise ValueError("due before issued")
        return values


def to_row(inv: Invoice) -> dict:
    return inv.dict()
```

## Steps

1. **Versions**: `uv pip show pydantic` gave `Version: 2.13.5`.
2. **Baseline**: `uv run pytest -q` gave `2 passed, 5 warnings`. The
   warnings summary named each v1 use: `invoice.py:15` `@validator`,
   `:19` `@root_validator`, `:6` class-based `config`, a `UserWarning`
   `Valid config keys have changed in V2` (for `orm_mode`), and `:27`
   `The dict method is deprecated`.
3. **As errors**, to prove the list complete later:
   `uv run pytest -q -W error::pydantic.warnings.PydanticDeprecatedSince20`
   gave `1 error in 0.12s` (collection stopped at the first).
4. **Probe the current behaviour** of the before validator
   (`core/probe.md`), `probe_currency.py`:
   ```
   'eur' -> EUR
   978 -> CRASH AttributeError 'int' object has no attribute 'upper'
   None -> CRASH AttributeError 'NoneType' object has no attribute 'upper'
   ```
   The crash is existing behaviour; the ask is to keep behaviour, so it
   is reported, not fixed.
5. **Migrate** with `reference/v1-to-v2.md`:

```python
class Invoice(BaseModel):
    model_config = ConfigDict(from_attributes=True)       # orm_mode

    number: str
    currency: str
    issued: date
    due: date

    @field_validator("currency", mode="before")          # pre=True
    @classmethod
    def upper_currency(cls, v: Any) -> Any:
        return v.upper()

    @model_validator(mode="after")                       # root_validator
    def due_after_issued(self) -> "Invoice":
        if self.due < self.issued:                       # attributes, not values[...]
            raise ValueError("due before issued")
        return self


def to_row(inv: Invoice) -> dict:
    return inv.model_dump()                              # .dict()
```

6. **Check**: `uv run pytest -q` gave `2 passed in 0.07s` with no
   warnings; with `-W error::pydantic.warnings.PydanticDeprecatedSince20`,
   `2 passed in 0.05s`. The probe printed the same three lines as
   before. `from_attributes` still works: `Invoice.model_validate(row)`
   on a dataclass row gave `currency='EUR'`.
7. **Behaviour v2 changed on its own** (`core/migrate.md`): probed with
   the bundled `pydantic.v1`, `number=1001` gave `'1001'` in v1 and
   `string_type` at `('number',)` in v2. No test covers it; callers
   that send numbers would now get a 422.

## The answer

```
## Result
billing/invoice.py is v2: model_config with from_attributes, a before
field_validator, an after model_validator, model_dump. Behaviour kept,
with two findings:
- an int invoice number is now rejected (string_type); v1 turned 1001
  into '1001'. If callers send numbers, add
  Field(coerce_numbers_to_str=True) to number; say if you want it.
- upper_currency crashes on a non-string (AttributeError, a 500), in v1
  and v2 alike. Guarding it with isinstance(v, str) would make that a
  422; not done, as the ask was to keep behaviour.

## Checked
- uv run pytest -q: before 2 passed, 5 warnings; after 2 passed.
- uv run pytest -q -W error::pydantic.warnings.PydanticDeprecatedSince20:
  before 1 error in collection; after 2 passed.
- probe_currency.py: same output before and after.
- pydantic 2.13.5.

## Not checked
- Other modules calling .dict() on Invoice: searched src/, none.
```
