# Migrate v1 code to v2, or read it

**Verdict you produce:** each change with its v1 and v2 names, and the
test run that shows behaviour kept.

```
<file:line>  <v1 name>  ->  <v2 name>     (one line per change)
behaviour:   <what changed on purpose, or "none">
tests:       <command> -> <summary line>, before and after
warnings:    <run with PydanticDeprecatedSince20 as an error: clean>
```

## Find every v1 use

1. Let pydantic list them. v1 names still work in 2.13.5 but warn with
   `PydanticDeprecatedSince20`; turn the warning into an error:

```
uv run pytest -q -W error::pydantic.warnings.PydanticDeprecatedSince20
```

   *lab:* the collection stopped at the first `@validator` with
   `ERROR tests/test_product.py - pydantic.warnings.PydanticDeprecatedSince20`.
   A plain `uv run pytest` lists each in its warnings summary with file
   and line.
2. Search for what does not warn, or runs only in some paths
   (navigation owns searching; these are the patterns):

```
@validator  @root_validator  .dict(  .json(  parse_obj  parse_raw
class Config  orm_mode  allow_mutation  __fields__  regex=  const=
update_forward_refs  from_orm  .copy(  pydantic.v1
```

## Change, in this order

1. Config: `class Config:` becomes `model_config = ConfigDict(...)`;
   renamed keys in `reference/v1-to-v2.md`. Do this first: *lab:* a
   class with both fails with `"Config" and "model_config" cannot be
   used together`.
2. Validators: `@validator("x")` becomes `@field_validator("x")` plus
   `@classmethod`; `pre=True` becomes `mode="before"`; `always=True`
   becomes `Field(validate_default=True)`; `each_item=True` has no
   argument in v2 (*lab:* `field_validator` takes `mode`, `check_fields`
   and `json_schema_input_type` only): put the check on the item type
   with `Annotated` (`typing/annotated.md`).
   `@root_validator(pre=True)` becomes `@model_validator(mode="before")`
   as a classmethod; a post root validator becomes
   `@model_validator(mode="after")`, an instance method that returns
   `self` and reads fields as attributes, not from `values`.
3. Methods: `.dict()` to `.model_dump()`, `.json()` to
   `.model_dump_json()`, `parse_obj` to `model_validate`, the rest in
   `reference/v1-to-v2.md`.
4. Field arguments: `regex=` to `pattern=`, `const=` to a `Literal`
   type, `min_items`/`max_items` to `min_length`/`max_length`, extra
   keyword arguments to `json_schema_extra={...}`.
5. Run the tests after each step, and the warning check at the end.

## Behaviour that changed silently

Checked against the v1 bundled in 2.13.5 (`pydantic.v1`, 1.10.26):

| Input | v1 | v2 (2.13.5) |
| --- | --- | --- |
| `Optional[str]` field left out | `None` | `missing`: required unless it has a default |
| `5` into a `str` field | `'5'` | `string_type` |
| `"1"` into `Union[int, str]` | `1` (first member that converts) | `'1'` (exact type wins: smart mode) |
| `class Config: allow_mutation = False` | frozen | **not frozen**: only `UserWarning: 'allow_mutation' has been removed`; use `frozen=True` |

Each is a behaviour change: say which ones the migration keeps, and add
a test for each kept one. To keep v1's conversion for one field, see
`typing/strict-and-lax.md` (`coerce_numbers_to_str`).

## `pydantic.v1`

`from pydantic.v1 import BaseModel` gives the old API inside pydantic 2
(1.10.26 in 2.13.5; no warning on Python 3.12, *lab*). It is a step in a
migration, file by file, never the target for new code. v1 and v2 models
do not mix: *lab:* a v1 model as a field of a v2 model failed with
`TypeError: BaseModel.validate() takes 2 positional arguments but 3 were
given`.

## Reading v1 code without migrating

Translate each name with `reference/v1-to-v2.md`, and remember the
table above: v1 code often relies on the conversions v2 removed. When
explaining v1 code, run it with `pydantic.v1` to show what it did.

## Never

- Never add new `@validator` or `.dict()` calls to match old code
  nearby; write v2 and offer to migrate the rest.
- Never silence `PydanticDeprecatedSince20` in the test configuration to
  finish a migration.
