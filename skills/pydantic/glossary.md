# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| model | A class that inherits `pydantic.BaseModel`; its annotated class attributes are its fields. |
| field | One annotated attribute of a model, described by a `FieldInfo` in `Model.model_fields`. |
| required | A field with no default: leaving it out of the input fails with `missing`. |
| nullable | A field whose type admits `None` (`X \| None`, `Optional[X]`); it says nothing about being required. |
| default | The value a field takes when the input leaves it out: `= value` or `Field(default_factory=...)`. |
| constraint | A limit checked by pydantic's core, such as `min_length`, `gt`, `pattern`, set in `Field()` or `Annotated`. |
| alias | Another name for a field in input and output: `Field(alias=)`, or `validation_alias` and `serialization_alias` separately, or an `alias_generator`. |
| probe | A short script, written to a file and run with `uv run --no-sync python`, that settles one question with output. |
| validator | A function that checks or changes a value during validation, attached with `field_validator`, `model_validator` or `Annotated`. |
| mode | When a validator runs: `before` (raw input), `after` (typed value, the default), `wrap` (around the core, with a `handler`), `plain` (instead of the core). |
| serializer | A function that changes how a value is dumped: `field_serializer`, `model_serializer`, `PlainSerializer`. |
| computed field | A property marked `@computed_field`, included in dumps and the schema but never read from input. |
| dump | The output of `model_dump()` (a dict) or `model_dump_json()` (a JSON string). |
| lax mode | The default: some inputs are converted, such as `"1"` into `1`; an `int` is not converted into `str`. |
| strict mode | No conversion: the input must already have the field's type (JSON strings for dates excepted). |
| smart union | A union validated against every member, picking the best match; on a tie the first member wins. |
| discriminated union | A union whose members are chosen by one `Literal` field (the discriminator), named in `Field(discriminator=)`. |
| forward reference | A type annotation naming a class that does not exist yet where it is written, as a string or under `from __future__ import annotations`. |
| rebuild | `Model.model_rebuild()`: build the model again once the names its annotations use exist. |
| `ValidationError` | The exception validation raises: a list of errors, each with `type`, `loc`, `msg` and `input`. |
| error type | The machine name of one error, such as `missing` or `string_too_short`; stable across messages. |
| `loc` | The path to the failing value: field names (aliases when set), list indexes, union member names. |
| schema error | An error raised when the model class is built or first used, not during validation, such as `PydanticUserError` or `PydanticSchemaGenerationError`. |
| `TypeAdapter` | pydantic's validator and dumper for a type that is not a model, such as `list[int]`. |
| settings class | A class that inherits `pydantic_settings.BaseSettings`, whose fields are read from sources. |
| source | One place a settings class reads values from: init arguments, environment, `.env` file, secrets directory, or a custom one. |
| source order | The priority of the sources, highest first, returned by `settings_customise_sources`. |
| prefix | `env_prefix`, the text put before a field's name to form its variable name, such as `APP_`. |
| nested delimiter | `env_nested_delimiter`, the text that splits a variable name into a path, such as `__` in `APP_DB__HOST`. |
| secrets directory | `secrets_dir`, a folder where each file's name is a variable name and its content the value. |
| trace | Finding which source set a setting's value and which others also set it. |
| partial model | A copy of a model made by pydantic-partial in which required fields accept `None` and default to `None`. |
| mixin | `pydantic_partial.PartialModelMixin`, the base class that gives a model `model_as_partial()` and lets a recursive partial reach it. |
| set field | A field present in the input, listed in `model_fields_set`, even when its value is `None`. |
| unset field | A field the input left out; `model_dump(exclude_unset=True)` omits it. |
| patch | The nested dict of set fields, `patch.model_dump(exclude_unset=True)`. |
| merge | Applying a patch to the stored model's dump: nested dicts key by key, anything else replaced. |
| hand-off | What pydantic gives the endpoint and the store after a PATCH: the validated full model and the changes. |
