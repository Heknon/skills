# `Annotated`: constraints and validators on a type

`Annotated[T, ...]` attaches constraints and validators to a type, so
the same rule can be reused by many fields, by list items and by
`TypeAdapter`.

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, Field

Sku = Annotated[str, Field(min_length=3, max_length=12, pattern=r"^[A-Z0-9-]+$")]
Trimmed = Annotated[str, BeforeValidator(lambda v: v.strip() if isinstance(v, str) else v)]
Upper = Annotated[str, AfterValidator(str.upper)]

class Product(BaseModel):
    sku: Sku
    name: Trimmed
    code: Upper
```

*lab (2.13.5):* `Product(sku="AB-1", name="  x ", code="ab")` gave
`sku='AB-1' name='x' code='AB'`; `sku="a", name=1, code=2` gave
`string_too_short`, `string_type`, `string_type`.

## Constraints

`Field(min_length=3)` on the assignment and `Annotated[str,
Field(min_length=3)]` in the type are the same to pydantic: both end up
in `Model.model_fields[name].metadata` (*lab:* `[MinLen(min_length=3)]`).
The `Annotated` form can be named and reused; `StringConstraints(...)`
bundles string rules the same way, with one trap: *lab:* with
`strip_whitespace=True, to_upper=True, pattern=r"^[A-Z]+$"`, `" AB "`
passed (stripped first) but `"ab"` failed with
`string_pattern_mismatch`: the pattern is checked before `to_upper`.
`conint(gt=0)` and friends are the
older spelling of the same thing (*lab:* `conint(gt=0)` is
`Annotated[int, ..., Interval(gt=0, ...)]`).

Available on `Field`, *lab* signature: `gt, ge, lt, le, multiple_of,
allow_inf_nan, max_digits, decimal_places, min_length, max_length,
pattern, strict, coerce_numbers_to_str, union_mode, fail_fast`.

## Validators in `Annotated`

`BeforeValidator`, `AfterValidator`, `WrapValidator` and
`PlainValidator` take a plain function (no `cls`). The order is not the
order written:

```python
x: Annotated[int, AfterValidator(a1), AfterValidator(a2),
             BeforeValidator(b1), BeforeValidator(b2)]
```

*lab:* ran `before2, before1, after1, after2`: before validators from
right to left, then the core check, then after validators from left to
right.

## On list items and dict values

A validator on the item type runs per item, which replaces v1's
`each_item=True`:

```python
def not_blank(v: str) -> str:
    if not v.strip():
        raise ValueError("blank")
    return v

class Tags(BaseModel):
    tags: list[Annotated[str, AfterValidator(not_blank)]]
```

*lab:* `["a", " ", "b"]` gave `value_error` at `('tags', 1)`: the `loc`
names the item.

## With `None`

Put the constraint inside the optional part so `None` stays allowed:
`Optional[Annotated[str, Field(min_length=2)]]`. *lab:* `"a"` gave
`string_too_short`, `None` passed.
