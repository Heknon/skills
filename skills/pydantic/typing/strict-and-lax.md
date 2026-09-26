# Strict and lax

## Lax, the default: what is converted

*lab (2.13.5):*

| Field | Input | Result |
| --- | --- | --- |
| `int` | `"1"` | `1` |
| `int` | `1.0` | `1` |
| `int` | `1.5` | `int_from_float` |
| `float` | `"1.5"` | `1.5` |
| `bool` | `"yes"`, `"on"`, `1` | `True` |
| `bool` | `"2"` | `bool_parsing` |
| `str` | `1` | `string_type`: **numbers are not turned into strings** |
| `datetime` | `"2026-01-01T03:04:05Z"` | a `datetime` with UTC |

v1 turned `5` into `'5'`; v2 does not. Where old data needs it:
`ConfigDict(coerce_numbers_to_str=True)` for the model, or
`Field(coerce_numbers_to_str=True)` for one field (*lab:* `5` became
`'5'`, `1.5` became `'1.5'`; another `str` field in the same model still
gave `string_type`).

## Strict: nothing is converted

| Scope | Write |
| --- | --- |
| whole model | `model_config = ConfigDict(strict=True)` |
| one field | `Field(strict=True)` or a type such as `StrictInt`, `StrictStr` |
| one call | `Model.model_validate(data, strict=True)` |

*lab:*

| Strict case | Result |
| --- | --- |
| `n: int`, input `"1"` (Python) | `int_type` |
| `when: datetime`, input `"2026-01-01T00:00:00"` (Python) | `datetime_type` |
| the same through `model_validate_json` | accepted: in JSON a date can only be a string, so strict JSON still parses it |

Use strict where a conversion would hide a client bug (an ID sent as a
string); keep lax where input comes from forms, query strings or
environment variables, which are all strings. Settings classes rely on
lax mode: `APP_PORT=8000` is the string `"8000"`.
