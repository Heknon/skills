# Config keys and their defaults

Read from the installed source, pydantic 2.13.5
(`pydantic/_internal/_config.py`, `config_defaults`) and
pydantic-settings 2.15.0 (`pydantic_settings/main.py`,
`BaseSettings.model_config`). To read them on the installed version:

```python
from pydantic._internal._config import config_defaults   # private, read-only use
print(config_defaults)
from pydantic_settings import BaseSettings
print(BaseSettings.model_config)
```

## `ConfigDict` (models)

| Key | Default | Added | Note |
| --- | --- | --- | --- |
| `extra` | `None` (acts as `"ignore"`) | | `"forbid"`, `"allow"` |
| `frozen` | `False` | | v1 `allow_mutation=False` |
| `validate_assignment` | `False` | | |
| `validate_default` | `False` | | |
| `strict` | `False` | | `typing/strict-and-lax.md` |
| `from_attributes` | `False` | | v1 `orm_mode` |
| `populate_by_name` | `False` | | docstring: not recommended from 2.11, deprecated in v3 |
| `validate_by_alias` | `True` | 2.11 | |
| `validate_by_name` | `False` | 2.11 | at least one of the two must be `True` |
| `serialize_by_alias` | `False` | 2.11 | ignored silently on 2.10 (*lab*) |
| `alias_generator` | `None` | | `pydantic.alias_generators.to_camel` |
| `loc_by_alias` | `True` | | error `loc` uses aliases |
| `str_strip_whitespace`, `str_to_lower`, `str_to_upper` | `False` | | |
| `str_min_length`, `str_max_length` | `0`, `None` | | |
| `arbitrary_types_allowed` | `False` | | |
| `use_enum_values` | `False` | | store `.value`, not the member |
| `coerce_numbers_to_str` | `False` | | |
| `hide_input_in_errors` | `False` | | |
| `revalidate_instances` | `'never'` | | `'always'`, `'subclass-instances'` |
| `protected_namespaces` | `('model_validate', 'model_dump')` | | *lab:* a field `model_dump_x` warned `conflicts with protected namespace 'model_dump'` |
| `ser_json_timedelta` | `'iso8601'` | | |
| `ser_json_temporal` | `'iso8601'` | 2.12 | |
| `val_temporal_unit` | `'infer'` | 2.12 | |
| `ser_json_bytes`, `val_json_bytes` | `'utf8'` | `val_`: 2.9 | |
| `ser_json_inf_nan` | `'null'` | | |
| `allow_inf_nan` | `True` | | |
| `regex_engine` | `'rust-regex'` | | *lab:* a look-ahead `pattern` failed with `SchemaError` until `'python-re'` |
| `validation_error_cause` | `False` | 2.5 | |
| `use_attribute_docstrings` | `False` | 2.7 | |
| `cache_strings` | `True` | 2.7 | |
| `json_schema_serialization_defaults_required` | `False` | 2.4 | |
| `json_schema_mode_override` | `None` | 2.4 | |
| `url_preserve_empty_path` | `False` | 2.12 | |
| `polymorphic_serialization` | `False` | 2.13 (not in 2.12.5's `ConfigDict`, *lab*) | |
| `defer_build` | `False` | | |
| `json_encoders` | `None` | | deprecated since 2.0, still read |
| `schema_generator` | `None` | | deprecated 2.10, no effect |

"Added" is from the `version-added` notes in the installed source; empty
means 2.0 or not stated.

A key a version does not know is not an error: *lab:*
`ConfigDict(serialize_by_alias=True)` on 2.10.6 dumped snake_case with
no warning. Check the table before relying on a newer key.

## `SettingsConfigDict` (`BaseSettings` defaults, 2.15.0)

| Key | Default | Note |
| --- | --- | --- |
| `extra` | `'forbid'` | unlike models; `settings/dotenv.md` |
| `validate_default` | `True` | unlike models |
| `arbitrary_types_allowed` | `True` | |
| `case_sensitive` | `False` | `settings/env.md` |
| `env_prefix` | `''` | |
| `env_prefix_target` | `'variable'` | 2.13+; `'alias'`, `'all'` |
| `env_file` | `None` | a path, or a tuple of paths |
| `env_file_encoding` | `None` (read as UTF-8) | |
| `dotenv_filtering` | not set | 2.14+; `'match_prefix'`, `'only_existing'` |
| `env_ignore_empty` | `False` | |
| `env_nested_delimiter` | `None` | |
| `env_nested_max_split` | `None` | |
| `env_parse_none_str` | `None` | |
| `env_parse_enums` | `None` | |
| `nested_model_default_partial_update` | `False` | |
| `secrets_dir` | `None` | a path, or several |
| `json_file`, `yaml_file`, `toml_file` | `None` | read only when that source is added (`settings/sources.md`) |
| `cli_parse_args` and the other `cli_` keys | `None` / `False` | the command-line source; not covered here |
| `protected_namespaces` | `('model_validate', 'model_dump', 'settings_customise_sources')` | |
| `enable_decoding` | `True` | JSON-decode complex values from variables |

Version columns for settings keys: `reference/versions.md`.
