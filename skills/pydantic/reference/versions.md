# What changed in each release

Only facts that were run in the lab or read in the installed source of
the version named. Check the installed versions first
(`uv pip show pydantic pydantic-settings pydantic-partial`). Pins of
this skill: Python 3.12, pydantic 2.13.5 (pydantic-core 2.46.5),
pydantic-settings 2.15.0, pydantic-partial 0.11.1.

## pydantic 2.10 to 2.13

Run on 2.10.6, 2.11.10, 2.12.5 and 2.13.5 (*lab*):

| Feature | 2.10 | 2.11 | 2.12 | 2.13 |
| --- | --- | --- | --- | --- |
| `ConfigDict(serialize_by_alias=True)` | **ignored silently** | yes | yes | yes |
| `ConfigDict(validate_by_name=True)` | ignored (construction by name fails with `missing`) | yes | yes | yes |
| `model_validate(..., by_alias=, by_name=)` | `TypeError` | yes | yes | yes |
| `m.model_fields` on an instance | fine | `PydanticDeprecatedSince211` | same | same |
| `Field(exclude_if=...)` | extra keyword warning, no effect | same | yes | yes |
| `model_dump(exclude_computed_fields=True)` | `TypeError` | `TypeError` | yes | yes |
| `model_validate(..., extra="forbid")` | `TypeError` | `TypeError` | yes | yes |
| `model_dump(..., fallback=)` | no | yes | yes | yes |
| `model_dump(..., polymorphic_serialization=)`, the config key | no | no | no | yes |
| smart union picks the model with more fields set | yes | yes | yes | yes |

Config keys by version: `reference/config.md`. Bundled v1:
`pydantic.v1.VERSION` is 1.10.26 in 2.13.5.

## pydantic-settings

Checked by importing each release (*lab*):

| Feature | First release that has it |
| --- | --- |
| default source order init, env, `.env`, secrets, defaults | the same on 2.8.1, 2.12.0 and 2.15.0 (run) |
| `NestedSecretsSettingsSource` | 2.12.0 (absent in 2.11.0) |
| `env_prefix_target` | 2.13 (absent in 2.12.0, present in 2.13.1) |
| `dotenv_filtering` | 2.14 (absent in 2.13.1, present in 2.14.1) |
| `PYDANTIC_SETTINGS_DEBUG` source logging | 2.15.0 (absent in 2.14.1) |

The trace script in `recipes/settings/` ran on 2.15.0 and 2.12.0.

## pydantic-partial

From each release's metadata and a diff of its `partial.py` and
`utils.py`; behaviour run on pydantic 2.13.5 (*lab*):

| Release | Requires | API | On pydantic 2.13.5 |
| --- | --- | --- | --- |
| 0.3.x | pydantic < 2 | `as_partial()` only, `__fields__` | cannot be installed |
| 0.5.0, 0.5.1 | pydantic < 2.1 (metadata; 0.5.0 refused by uv) | adds `model_as_partial()`; `as_partial()` warns | cannot be installed |
| 0.5.2 to 0.6.0 | pydantic < 3 | same; no `partial_cls_name` | works; each partial created warns `PydanticDeprecatedSince20: Using extra keyword arguments on Field is deprecated ... (Extra keys: 'metadata')`; `partial_cls_name=` gives `TypeError` |
| 0.7.0 | pydantic < 3 | adds `partial_cls_name`; starts to recognise `X \| None` (source) | **`TypeError: type 'types.UnionType' is not subscriptable`** for `recursive=True` on a model with an `X \| None` field |
| 0.8.0 | pydantic >= 2 (drops v1) | same | same `TypeError` |
| 0.9.0 | pydantic >= 2 | fixes the `UnionType` case; stops adding `nullable` to the schema (source) | works, with the `metadata` warning |
| 0.10.0 | pydantic >= 2, Python >= 3.10 | same | same |
| 0.10.2 | same | drops `metadata` from copied fields: the warning goes | works |
| 0.11.1 | same | same code as 0.10.2 | works |

On every release that installs (0.5.2 to 0.11.1; 0.7.0 and 0.8.0 with
`Optional[X]` instead of `X | None`), *lab*: required fields lose their
constraints, inherited validators receive `None`, and `recursive=True`
skips nested models without the mixin (`partial/validators.md`,
`partial/build.md`).
