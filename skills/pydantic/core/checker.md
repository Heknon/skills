# Why a checker flags a model

**Verdict you produce:** the message, the rule behind it, and the fix.

```
checker: <basedpyright | pyright | mypy (+ pydantic.mypy)> <version>
message: <file:line: the message and its rule code, verbatim>
rule:    <why the checker sees the model this way>
fix:     <the change>; rerun: <0 errors>
```

## Which checker you are looking at

In Zed, the squiggles under Python code come from **basedpyright** by
default since Zed 0.204.0, run in its `standard` mode, which matches
pyright's (Zed's own documentation, `docs/src/languages/python.md`, read
2026-09-26; *not run in Zed*). A project can change the mode in
`pyrightconfig.json` or `[tool.basedpyright]`/`[tool.pyright]` in
`pyproject.toml`. The linting skill owns that configuration and how to
run the checkers; this file says what their messages about models mean.

To see the same messages in the terminal, run the checker the project
has (`uv run pyright`, `uv run basedpyright`, `uv run mypy src`).
*lab:* basedpyright 1.40.1 ("based on pyright 1.1.414") gave the same
four errors as pyright 1.1.414 on the shapes below, plus warnings of its
own in its default `recommended` mode (such as `reportDeprecated` on
`Optional`).

## Steps

1. Copy the message verbatim with its rule code (`reportCallIssue`,
   `[call-arg]`).
2. Find its row in `typing/checkers.md`: most messages about models come
   from the checker seeing the generated `__init__` differently from
   pydantic at run time.
3. Decide which side is right. Either the code is wrong (fix the code),
   or the checker cannot know something true at run time (make the code
   say it in a form the checker reads).
4. Fix, rerun the checker, rerun the tests.

## The usual cases (*lab*, pydantic 2.13.5, pyright 1.1.414, mypy 2.3.1)

| Message | Rule behind it | Fix |
| --- | --- | --- |
| pyright: `No parameter named "amount_cents"` and `Argument missing for parameter "amountCents"` | `Field(alias=...)` names the `__init__` parameter; `populate_by_name` is invisible to checkers | `Field(validation_alias="amountCents", serialization_alias="amountCents")` keeps the field name as the parameter; or pass the alias |
| pyright or mypy: `Argument missing for parameter "nickname"` / `Missing named argument "nickname"` | the field is `Optional` with no default: it **is** required | add `= None` if it may be omitted; otherwise pass it |
| pyright, mypy without the plugin: `Argument of type "Literal['5']" cannot be assigned to parameter "n" of type "int"` | checkers do not know lax mode converts `"5"` | pass an `int`, or parse untyped data with `Model.model_validate(data)` |
| pyright, mypy without the plugin: `Argument missing for parameter "db_password"` on `Settings()` | settings fields are filled from sources the checker cannot see | mypy: the `pydantic.mypy` plugin accepts it; pyright: `Settings()  # pyright: ignore[reportCallIssue]` with a comment naming the source |
| pyright: `Argument missing for parameter "id"` on `UserPatch(name="x")` | a pydantic-partial class is typed as the full model | parse bodies with `UserPatch.model_validate(body)` |
| mypy: `Unsupported dynamic base class "User.model_as_partial"` | `class UserPatch(User.model_as_partial())` | `create_model("UserPatch", __base__=User.model_as_partial())` (`partial/build.md`) |

## Suppressing, when it is truly the checker's blind spot

Only with the rule named and a reason on the line:

```python
settings = Settings()  # pyright: ignore[reportCallIssue]  # filled from APP_ variables
```

Never a bare `# type: ignore`: *lab:* it silenced the alias errors
above and would silence any later error on that line too. Never `cast`,
and never make a field `Optional` to please the checker: that changes
what the model accepts.

## Verdict check

The fix is done when the checker reports `0 errors` for the file and the
tests still pass. Quote both lines.
