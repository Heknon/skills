# Check the installed pydantic-partial first

**Verdict you produce**, before any partial model code is written:

```
pydantic-partial: <version>, at <path to partial.py>
model_as_partial(<the parameters its signature lists>)
known problems on this version: <from the table below>
```

pydantic-partial renamed and added things between releases, and the
names look alike. Code written for another release fails with
`TypeError` or `AttributeError`, or works but warns.

## 1. The version and the file

```
uv pip show pydantic-partial
uv run --no-sync python -c "import pydantic_partial.partial as p; print(p.__file__)"
```

*lab:* `Version: 0.5.5`, and the path
`.venv/lib/python3.12/site-packages/pydantic_partial/partial.py`
(`.venv\Lib\site-packages\...` on Windows). If `uv pip show` prints
`warning: Package(s) not found for: pydantic-partial`, it is not
installed: say so, and do not add it unasked (air gapped). How to read
an installed package in general is the offline-docs skill's ground.

## 2. Read `partial.py`

It is under 200 lines on every release (145 to 180). Read the
signature of `model_as_partial` and the body of `create_partial_model`:

| Look for | Tells you |
| --- | --- |
| `def model_as_partial(cls, *fields, recursive=False, partial_cls_name=None)` | 0.7.0 or later: `partial_cls_name` exists |
| `def model_as_partial(cls, *fields, recursive=False)` | 0.5.x or 0.6.0: no `partial_cls_name` (*lab:* `TypeError: PartialModelMixin.model_as_partial() got an unexpected keyword argument 'partial_cls_name'`) |
| `def as_partial` that calls `warnings.warn` | deprecated alias: *lab:* `as_partial(...) is deprecated, use model_as_partial(...) instead` |
| `issubclass(field_annotation, PartialModelMixin)` | `recursive` only reaches nested models with the mixin |
| `if field_info.is_required()` | only required fields are made optional; fields with defaults keep them |
| `"metadata"` in the `copy_field_info` exclusions (`utils.py`) | 0.10.2 or later; constraints are dropped either way (`partial/validators.md`) |

## 3. The API by release (*lab*, on pydantic 2.13.5)

| Release | Use | Do not use |
| --- | --- | --- |
| 0.9.0 to 0.11.1 | `Model.model_as_partial(*fields, recursive=, partial_cls_name=)`, `create_partial_model(Model, ...)` | `as_partial` (warns) |
| 0.7.0, 0.8.0 | the same, but `recursive=True` on a model with an `X \| None` field crashes: `TypeError: type 'types.UnionType' is not subscriptable`; write `Optional[X]` there | |
| 0.5.2 to 0.6.0 | `model_as_partial(*fields, recursive=)`; name the class with `create_model` (`partial/build.md`) | `partial_cls_name` |
| 0.3.x, 0.5.0, 0.5.1 | cannot be installed with pydantic 2.13 | |

There is no `Model.partial()` and no `Partial[Model]`: *lab:* on 0.5.5
to 0.11.1 the package exports only `PartialModelMixin` and
`create_partial_model`, and `hasattr(Item, "partial")` was `False`.
`create_partial_model(Model)` also works on a plain `BaseModel` without
the mixin (*lab*), but only the mixin lets a recursive partial reach a
nested model.

Full release notes: `reference/versions.md`.
