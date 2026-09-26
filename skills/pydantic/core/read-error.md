# Read an error

**Verdict you produce:** for each error, where it is, what failed, and
the line that raised it.

```
error:  <loc> : <type> : <input>      (one line per error)
raised: <file:line of the model_validate / constructor call>
cause:  <the rule that rejected it: the field's type, a constraint, a validator>
```

Decide first which of three things you have.

## 1. A `ValidationError`: the input was wrong

*lab (2.13.5)*, `Order.model_validate({"id": "x", "lines": [{"sku":
"A", "qty": 0}, {"qty": "2"}], "note": "hi"})` with `extra="forbid"`:

```
4 validation errors for Order
id
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='x', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/int_parsing
lines.0.qty
  Input should be greater than 0 [type=greater_than, input_value=0, input_type=int]
lines.1.sku
  Field required [type=missing, input_value={'qty': '2'}, input_type=dict]
note
  Extra inputs are not permitted [type=extra_forbidden, input_value='hi', input_type=str]
```

(Each block ends with such a URL line; the later ones are left out
here.) Read each block as: the path (`lines.0.qty` is the first line's `qty`),
the message, then `type` in brackets. For `missing`, `input_value` is
the **parent** object that lacks the key. The URL cannot be reached air
gapped; the `type` is what to look up (`reference/errors.md`).

The same as data, which is what to print in a probe:

```python
e.errors()      # list of dicts: type, loc, msg, input, ctx (some), url
e.errors(include_url=False, include_input=False, include_context=False)
e.error_count() # 4
e.title         # 'Order'
```

*lab:* `{'type': 'greater_than', 'loc': ('lines', 0, 'qty'), 'msg':
'Input should be greater than 0', 'input': 0, 'ctx': {'gt': 0}}`.

What a `loc` can hold:

| `loc` part | Means |
| --- | --- |
| a field name, or its alias when aliases exist | that field (*lab:* `('orderId',)` with `alias_generator=to_camel`) |
| an integer | a list or tuple index |
| a model's class name, such as `'Dog2'` | a member of a plain union, tried in turn |
| a tag, such as `'cat'` | a member of a discriminated union |
| `()` empty | the whole object: a `model_validator`, or invalid JSON (`json_invalid`) |

When the input is a secret, `hide_input_in_errors=True` in the config
drops `input_value` from the text (*lab*).

## 2. A crash inside validation: the code was wrong

A traceback that is **not** `ValidationError` but passes through
`pydantic/main.py` `__init__` or `model_validate` came from a validator
or serializer:

```
AttributeError: 'int' object has no attribute 'strip'
```

*lab:* a `before` validator calling `.strip()` on `42`. Only
`ValueError`, `AssertionError` and `PydanticCustomError` become
validation errors (`core/validate.md`). The fix is in the validator, not
in the caller's `except`.

## 3. A schema error: the model itself was wrong

Raised when the class is defined, first used, or rebuilt; the input
does not matter.

| Exception, *lab* message | Cause | Go to |
| --- | --- | --- |
| `PydanticUserError`: `` `Order` is not fully defined; you should define `Customer`, then call `Order.model_rebuild()`. `` | a forward reference not resolved | `typing/forward-refs.md` |
| `PydanticUndefinedAnnotation`: `name 'Customer' is not defined` | `model_rebuild()` called where the name does not exist | `typing/forward-refs.md` |
| `PydanticSchemaGenerationError`: ``Unable to generate pydantic-core schema for <class 'Thing'>. Set `arbitrary_types_allowed=True`...`` | a field type pydantic does not know | `typing/type-adapter.md` |
| `PydanticUserError`: ``"Config" and "model_config" cannot be used together`` | v1 and v2 config mixed | `core/migrate.md` |
| `PydanticUserError`: `` `regex` is removed. use `pattern` instead `` | a v1 keyword | `reference/v1-to-v2.md` |
| `PydanticUserError`: `If you use @root_validator with pre=False (the default) you MUST specify skip_on_failure=True` | a v1 root validator | `core/migrate.md` |

`PydanticUserError` carries a `code` (such as `class-not-fully-defined`);
`reference/errors.md` lists all 48 on 2.13.5.

## Then

Find the line that raised it: the last frame in your code above the
pydantic frames. Say whether the input or the model must change. In a
web service, turning a `ValidationError` into a 422 response is the api
skill's ground.
