# Error types

Each validation error has a `type`; the message may change between
versions, the type does not. The URL in the message cannot be reached
air gapped.

## Seen in the lab (2.13.5, 2.15.0)

| `type` | Message | Typical cause |
| --- | --- | --- |
| `missing` | `Field required` | no default and not in the input; `loc` names the field |
| `extra_forbidden` | `Extra inputs are not permitted` | a key no field matches, with `extra="forbid"` (the settings default) |
| `string_type` | `Input should be a valid string` | a number, `None` or a list into `str` |
| `int_parsing` | `Input should be a valid integer, unable to parse string as an integer` | `"x"` into `int`; also `""` from an empty variable |
| `int_from_float` | | `1.5` into `int` |
| `int_type` | `Input should be a valid integer` | `"1"` into `int` in strict mode |
| `bool_parsing` | | `"2"` into `bool` |
| `datetime_type` | `Input should be a valid datetime` | a string into `datetime` in strict Python mode |
| `string_too_short`, `string_too_long` | `String should have at least 3 characters` | `min_length`, `max_length` |
| `string_pattern_mismatch` | `String should match pattern '^[A-Z]+$'` | `pattern` |
| `greater_than` | `Input should be greater than 0` | `gt`; `ctx` holds `{'gt': 0}` |
| `literal_error` | | a value outside a `Literal` |
| `union_tag_invalid` | `Input tag 'cow' found using 'type' does not match any of the expected tags: 'dog', 'cat'` | discriminated union, unknown tag |
| `union_tag_not_found` | | discriminated union, tag field missing |
| `model_type` | | a non-dict into a model, or an object without `from_attributes` |
| `is_instance_of` | `Input should be an instance of Thing` | `arbitrary_types_allowed` field |
| `frozen_instance`, `frozen_field` | `Instance is frozen` | assignment to a frozen model or field |
| `value_error` | `Value error, <your text>` | `ValueError` raised in a validator |
| `assertion_error` | `Assertion failed, <your text>` | `assert` in a validator |
| `json_invalid` | `Invalid JSON: expected value at line 1 column 21` | `model_validate_json` on broken JSON; `loc` is `()` |
| your own | your template | `PydanticCustomError("type", "template {x}", {"x": ...})` |

## All of them, on the installed version

```python
from typing import get_args
from pydantic_core.core_schema import ErrorType
print(get_args(ErrorType))            # 104 names on pydantic-core 2.46.5

from pydantic.errors import PydanticErrorCodes
print(get_args(PydanticErrorCodes))   # 48 codes of PydanticUserError on 2.13.5
```

## `PydanticUserError` codes worth knowing

Raised when a model is built or rebuilt (`core/read-error.md`, part 3).
*lab* message for each:

| `code` | Message starts |
| --- | --- |
| `class-not-fully-defined` | `` `Order` is not fully defined; you should define `Customer`, then call `Order.model_rebuild()` `` |
| `config-both` | `"Config" and "model_config" cannot be used together` |
| `removed-kwargs` | `` `regex` is removed. use `pattern` instead ``, `` `const` is removed, use `Literal` instead `` |
| `root-validator-pre-skip` | `If you use @root_validator with pre=False (the default) you MUST specify skip_on_failure=True` |

Others by name only (from `PydanticErrorCodes`): `discriminator-no-field`,
`discriminator-needs-literal`, `model-field-overridden`,
`model-field-missing-annotation`, `undefined-annotation`,
`schema-for-unknown-type`, `validator-signature`,
`field-serializer-signature`, `validate-by-alias-and-name-false`.

## Not a validation error

| Exception | Where from |
| --- | --- |
| `AttributeError`, `TypeError`, any other | your validator or serializer; it escapes (`core/validate.md`) |
| `PydanticSchemaGenerationError` | a type pydantic cannot build a schema for |
| `PydanticUndefinedAnnotation` | `model_rebuild()` where a name is still missing |
| `pydantic_settings.SettingsError` | `error parsing value for field "hosts" from source "EnvSettingsSource"`: a variable that should be JSON is not (`settings/env.md`) |
| `UnicodeDecodeError` | a `.env` file that is not UTF-8 (`settings/dotenv.md`) |
