# The pydantic mypy plugin

**What it decides:** whether mypy reads pydantic models correctly, and
how to turn the plugin on. Verified on mypy 2.3.1 with pydantic 2.13.5.
What a model's types mean (`Annotated`, generics, discriminated unions,
`Optional` against a default) is the pydantic skill's.

## Turning it on

```toml
[tool.mypy]
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
```

In `mypy.ini`: `plugins = pydantic.mypy` under `[mypy]`, and a
`[pydantic-mypy]` section with `True`. The plugin ships inside pydantic
(the installed package's `mypy.py`), so nothing is installed. Its
settings, read in that file: `init_forbid_extra` (no `**kwargs` in
`__init__`), `init_typed` (typed `__init__` arguments),
`warn_required_dynamic_aliases`, and `debug_dataclass_transform` (for
pydantic's own tests).

## What changes, on one model

```python
class User(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    id: int
    name: str = Field(alias="userName")
```

All of these ran without error at runtime (pydantic accepts the field
name because of `validate_by_name=True`, and coerces `"7"` in lax mode):

| Call | No plugin | Plugin, no settings | Plugin with the three settings |
| --- | --- | --- | --- |
| `User(id=1, name="x")` | `Unexpected keyword argument "name" for "User"  [call-arg]` | accepted | accepted |
| `User(id=1, userName="x")` | accepted | `Missing named argument "name" for "User"` | `Unexpected keyword argument "userName" for "User"` |
| `Order(user_id="7", total=3)` | `Argument "user_id" to "Order" has incompatible type "str"; expected "int"` | accepted (arguments are `Any`) | the same `arg-type` error |
| `Order(user_id=1, total=2.0, extra=1)` | `Unexpected keyword argument "extra"` | accepted (`**kwargs: Any`) | `Unexpected keyword argument "extra"` |
| `Order.model_construct(user_id="x")` | accepted | `Missing named argument "total" for "model_construct"` and the `arg-type` error | the same |

`reveal_type(Order.__init__)` shows why: without the plugin mypy builds
`__init__` from pydantic's `dataclass_transform`
(`def (self, *, user_id: int, total: float)`), which does not know
`validate_by_name`; the plugin builds it from the model's config.

## When mypy complains about a model

1. Run mypy and read the code: `call-arg` or `arg-type` on a model
   call is the usual sign.
2. Check the plugin is on in the config file mypy reads
   (`uv run --no-sync mypy -v ... | Select-String "Config File"`, then
   `plugins`).
3. Check the code at runtime: construct the model the way the code
   does. If it works and mypy disagrees, the plugin is the fix, not a
   `# type: ignore` and not a change of call sites.
4. If mypy is right with the plugin on, the error is real: for what the
   type should be, go to the pydantic skill.

pyright has no plugin. *Lab, pyright 1.1.414:* it rejected the same
three calls as mypy without the plugin (`No parameter named "name"
(reportCallIssue)`), so with `validate_by_name` it will always disagree
with the runtime; say so rather than change working code.

## pyright and basedpyright on pydantic code

*Lab,* pyright 1.1.414 and basedpyright 1.40.1 with pydantic 2.13.5 and
pydantic-settings 2.15.0, no config:

| Line | Finding | Fix |
| --- | --- | --- |
| `settings = Settings()`, a required field read from `APP_DB_PASSWORD` | both: `Argument missing for parameter "db_password" (reportCallIssue)`; mypy with the plugin: none | one narrow ignore naming the source: `settings = Settings()  # pyright: ignore[reportCallIssue]  # filled from APP_ variables` |
| `model_config = ConfigDict(extra="forbid")` | basedpyright only (its default mode, `recommended`): ``Type annotation for attribute `model_config` is required because this class is not decorated with `@final` (reportUnannotatedClassAttribute)`` | `model_config: ClassVar[ConfigDict] = ConfigDict(...)`, and `ClassVar[SettingsConfigDict]` on a `BaseSettings` |

With both fixes, pyright and basedpyright reported `0 errors`, mypy
with the plugin `Success: no issues found in 1 source file`, and at
runtime `extra="forbid"` still rejected an unknown field
(`extra_forbidden`). Never make the settings field optional or give it
a fake default to quiet the checker: that changes what the settings
accept. What a model's config means is the pydantic skill's
(`skills/pydantic/typing/checkers.md`).
