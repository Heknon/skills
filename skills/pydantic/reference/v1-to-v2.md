# v1 names and their v2 replacements

What each v1 name does on pydantic 2.13.5 (*lab*): **warns** means it
still works and emits `PydanticDeprecatedSince20` (a subclass of
`DeprecationWarning`); **fails** means an error when the class is built;
**silent** means it is accepted and does something else.

## Methods and attributes

| v1 | v2 | On 2.13.5 |
| --- | --- | --- |
| `m.dict()` | `m.model_dump()` | warns |
| `m.json()` | `m.model_dump_json()` | warns |
| `M.parse_obj(d)` | `M.model_validate(d)` | warns |
| `M.parse_raw(s)` | `M.model_validate_json(s)` | warns |
| `M.parse_file(p)` | read the file, then `model_validate_json` | warns |
| `M.from_orm(o)` | `M.model_validate(o)` with `from_attributes=True` | fails without it: `You must set the config attribute from_attributes=True to use from_orm` |
| `m.copy(update=)` | `m.model_copy(update=)` | warns; neither validates |
| `M.schema()` | `M.model_json_schema()` | warns |
| `M.construct()` | `M.model_construct()` | warns |
| `M.update_forward_refs()` | `M.model_rebuild()` | warns |
| `M.__fields__` | `M.model_fields` | warns |
| `m.__fields_set__` | `m.model_fields_set` | warns |
| `m.model_fields` on an instance | on the class | 2.11+: `PydanticDeprecatedSince211` |

## Validators

| v1 | v2 | On 2.13.5 |
| --- | --- | --- |
| `@validator("x")` | `@field_validator("x")` + `@classmethod` | warns |
| `@validator("x", pre=True)` | `@field_validator("x", mode="before")` | warns |
| `@validator("x", always=True)` | `Field(validate_default=True)` | warns |
| `@validator("x", each_item=True)` | `list[Annotated[T, AfterValidator(f)]]` | warns |
| `@root_validator` | `@model_validator(mode="after")`, returns `self` | fails: `If you use @root_validator with pre=False (the default) you MUST specify skip_on_failure=True` |
| `@root_validator(skip_on_failure=True)` | `@model_validator(mode="after")` | warns |
| `@root_validator(pre=True)` | `@model_validator(mode="before")` + `@classmethod` | warns |

## Config

| v1 | v2 | On 2.13.5 |
| --- | --- | --- |
| `class Config:` | `model_config = ConfigDict(...)` | warns: `Support for class-based config is deprecated` |
| both `class Config` and `model_config` | one of them | fails: `"Config" and "model_config" cannot be used together` |
| `orm_mode = True` | `from_attributes=True` | warns: `'orm_mode' has been renamed to 'from_attributes'` |
| `allow_mutation = False` | `frozen=True` | **silent**: warns `'allow_mutation' has been removed`, and the model is not frozen |
| `allow_population_by_field_name` | `validate_by_name=True` (2.11+) or `populate_by_name=True` | renamed (source) |
| `anystr_strip_whitespace`, `anystr_lower`, `anystr_upper` | `str_strip_whitespace`, `str_to_lower`, `str_to_upper` | renamed (source) |
| `min_anystr_length`, `max_anystr_length` | `str_min_length`, `str_max_length` | renamed (source) |
| `validate_all` | `validate_default` | renamed (source) |
| `schema_extra` | `json_schema_extra` | renamed (source) |
| `keep_untouched` | `ignored_types` | renamed (source) |
| `smart_union`, `fields`, `getter_dict`, `underscore_attrs_are_private`, `copy_on_model_validation`, `json_loads`, `json_dumps`, `error_msg_templates` | none | **silent**: removed (source), a warning only |
| `json_encoders` | `field_serializer` or `PlainSerializer` | still applied (*lab*), deprecated in the source |

## Field arguments

| v1 | v2 | On 2.13.5 |
| --- | --- | --- |
| `Field(regex=...)` | `Field(pattern=...)` | fails: `` `regex` is removed. use `pattern` instead `` |
| `Field(const=True)` | a `Literal[...]` type | fails: `` `const` is removed, use `Literal` instead `` |
| `Field(min_items=, max_items=)` | `min_length=`, `max_length=` | warns: `` `min_items` is deprecated and will be removed, use `min_length` instead `` |
| `Field(example=...)`, any unknown keyword | `Field(json_schema_extra={"example": ...})` | warns: `Using extra keyword arguments on Field is deprecated` |

## Types and imports

| v1 | v2 |
| --- | --- |
| `from pydantic import BaseSettings` | `from pydantic_settings import BaseSettings` (a separate package); *lab:* `PydanticImportError: BaseSettings has been moved to the pydantic-settings package` |
| `constr(regex=)`, `conint()` | `Annotated[str, Field(pattern=)]`, `Annotated[int, Field(gt=)]` |
| `pydantic.v1` | the v1 API inside 2.x, for migrating file by file |

Rows marked "source" come from `V2_RENAMED_KEYS` and `V2_REMOVED_KEYS`
in `pydantic/_internal/_config.py` (2.13.5), which drive the
`Valid config keys have changed in V2` warning; the others were run.
