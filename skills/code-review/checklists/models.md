# Models

Run when the change adds or changes a pydantic model, a field, a
validator, a serializer or settings (`core/checklist.md`). The pydantic
skill owns what each shape does; this pass asks whether the change
meant it. Probe a doubtful case in the project's interpreter
(pydantic: `core/probe.md`) rather than deciding from memory.

| ID | Ask | Sign | Facts (pydantic) | Default severity |
| --- | --- | --- | --- | --- |
| MOD1 | Did a field's required, nullable or default change, and do clients know? | `\| None`, `Optional[`, a changed default | `typing/required-and-optional.md` | major when a client's request now fails or a value silently changes |
| MOD2 | Does a PATCH tell "not sent" from `null`? | `exclude_unset`, `exclude_none`, `model_dump(` | `partial/unset-and-none.md` | blocker when fields are wiped |
| MOD3 | Does a validator run in the mode meant, return the value, raise the right error, and survive running twice? | `@field_validator`, `@model_validator` | `core/validate.md` | major |
| MOD4 | Does the wire shape change: alias, exclude, a computed field, a serializer? | `alias=`, `serialization_alias`, `@computed_field`, `exclude=` | `core/serialize.md`; api `core/compatibility.md` | major for a breaking shape |
| MOD5 | Are unknown keys ignored where a typo should be an error? | `extra=`, `model_config` | `reference/config.md`; api `core/review.md` | minor; major for PATCH |
| MOD6 | Does v2 code use v1 names? | `.dict()`, `parse_obj`, `@validator`, `class Config:`, `orm_mode` | `reference/v1-to-v2.md` | minor (deprecated), major when removed |
| MOD7 | Does a setting change its name, source or default? | `BaseSettings`, `env_prefix`, a changed default | `settings/sources.md`, `settings/trace.md` | major when a deployed value stops being read |

## Signs

```
MOD1  +  \|\s*None\b|Optional\[
MOD2  +  exclude_unset|exclude_none|model_dump\(
MOD3  +  @(field|model)_validator|@validator\b|@root_validator
MOD4  +  alias\s*=|serialization_alias|@computed_field|\bexclude\s*=
MOD5  +  \bextra\s*=|model_config
MOD6  +  \.dict\(\)|parse_obj|@validator\b|^\s*class Config\s*:|orm_mode
MOD7  +  BaseSettings|env_prefix|SettingsConfigDict
```
