# `TypeAdapter`: validating something that is not a model

`TypeAdapter(T)` gives a type the same validation, dumping and schema a
model has, without writing a model:

```python
from pydantic import TypeAdapter

ints = TypeAdapter(list[int])
ints.validate_python(["1", 2])          # [1, 2]
ints.validate_json('[1, "x"]')          # ValidationError: int_parsing at (1,)
TypeAdapter(dict[str, datetime]).dump_json({"a": datetime(2026, 1, 1)})
                                        # b'{"a":"2026-01-01T00:00:00"}'
TypeAdapter(PositiveInt).json_schema()  # {'exclusiveMinimum': 0, 'type': 'integer'}
```

(*lab*, 2.13.5.) The `loc` of an error starts at the top of the type:
`(1,)` is the second item of the list.

| Need | Use |
| --- | --- |
| validate a list of models from JSON | `TypeAdapter(list[Order]).validate_json(raw)` |
| a union or a discriminated union at the top level | `TypeAdapter(Pet)` where `Pet = Annotated[Union[...], Field(discriminator=...)]` |
| validate a `TypedDict`, a dataclass, a plain type | `TypeAdapter(T)` |
| dump plain data to JSON the way pydantic would | `TypeAdapter(T).dump_json(value)` (bytes) or `dump_python(value, mode="json")` |

`validate_python` takes `strict`, `from_attributes`, `context`,
`by_alias` and `by_name` like `model_validate` (*lab* signature).

## Types pydantic does not know

A field or adapter of an arbitrary class fails when the model is built:

```
PydanticSchemaGenerationError: Unable to generate pydantic-core schema
for <class '__main__.Thing'>. Set `arbitrary_types_allowed=True` in the
model_config to ignore this error ...
```

With `arbitrary_types_allowed=True`, pydantic only checks
`isinstance`: *lab:* `A(t=Thing())` passed, `A.model_validate({"t": 1})`
gave `is_instance_of`. Nothing is converted, and such a field cannot be
read from JSON. Prefer a real type (a model, a dataclass, `Annotated`
with validators) when the value comes from input.
