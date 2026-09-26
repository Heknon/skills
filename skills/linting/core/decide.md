# Fix, configure or suppress

**Verdict you produce:** one of three for each finding, with the reason.

```
finding:  src/greeting/banner.py:15: error: ... "str | None"; expected "str"  [arg-type]
decision: fix | configure | suppress
because:  <the docstring, the requirement, or why the checker is wrong here>
change:   <the diff, the config line, or the one comment>
```

## The order

1. **Fix the code** when the finding is true. This is the normal case.
2. **Configure** when the rule is wrong for the whole project or a whole
   folder: a rule the team does not want, tests that may `assert`, a
   package with no types. The change goes in the config file the tool
   reads (`core/config-files.md`), scoped as narrowly as the reason.
3. **Suppress one line** when the finding is true in general but wrong
   on this line, and a fix would make the code worse. One comment, with
   the code and a reason.

Changing the configuration or adding a suppression is a decision about
the project's rules. When the person asked only for green checks,
say which one you chose and why; for a project-wide rule change, ask.

## Fixing type errors without silencing them

A type error is fixed by making the value what the annotation says, not
by making the checker stop looking.

| Instead of | Do | Because |
| --- | --- | --- |
| `cast(str, user)` | handle `None`: `os.environ.get("APP_USER", "guest")`, or `if user is None:` with the behaviour the code needs | *lab:* the cast passed mypy and `banner()` returned `Welcome back, None!` |
| a parameter widened to `str \| None` | narrow at the caller, where the meaning of `None` is known | widening moves the problem into every caller |
| `Any`, or dropping an annotation | find the real type with `reveal_type` | `Any` turns the checks off for everything it touches |
| `# type: ignore` on a true error | fix it | the bug stays, and the next reader trusts the line |
| `assert x is not None` to narrow | an `if` with the behaviour; an `assert` only where `None` is impossible and you say why | `python -O` removes asserts; ruff's `S101` flags them |

When the checker is wrong (a missing plugin, a stub that lies, dynamic
code it cannot follow), fix what it reads: enable the plugin
(`mypy/pydantic.md`), add a stub (`mypy/stubs.md`), or suppress that
line with the code and why.

## Suppressing one line

The forms, each checked in the lab:

```python
from shop.pricing import price  # noqa: F401  # re-exported for plugins
value = greet(raw)  # type: ignore[arg-type]  # the stub for greet is wrong, see issue 42
value = greet(raw)  # pyright: ignore[reportArgumentType]  # same
value = greet(raw)  # type: ignore[arg-type]  # noqa: E501
```

- The code in brackets is required: bare `# noqa`, `# type: ignore`
  and `# pyright: ignore` silence everything on the line.
- `# noqa F401` without the colon is a bare `# noqa` (ruff's `PGH004`:
  `Use a colon when specifying noqa rule codes`); it silenced every rule
  on that line in the lab.
- mypy needs the reason after its own `#`: `# type: ignore[arg-type]
  stub is wrong` is `Invalid "type: ignore" comment  [syntax]`.
- mypy reads `# type: ignore` only as the first comment on the line;
  after `# noqa: E501  #` it was ignored. Put it first.
- pyright honours `# type: ignore[anything]` as a blanket ignore of the
  line, whatever the brackets say (*lab*). For a pyright-only project,
  use `# pyright: ignore[rule]`.
- A file-level `# ruff: noqa`, or `# ruff: disable[CODE]` without a
  matching `# ruff: enable[CODE]`, silences far more than one line
  (`ruff/suppression.md`).

Each tool can report suppressions that no longer suppress anything:
ruff `RUF100`, mypy `warn_unused_ignores`, pyright
`reportUnnecessaryTypeIgnoreComment`. Suggest them; add them to a
project only when asked.

## Never

- Never delete code a finding points at without checking who uses it:
  an "unused" import in `__init__.py` is often the package's public API
  (`ruff/suppression.md`).
- Never change a test, a public signature or behaviour to satisfy a
  checker unless that change is the fix and you say so.
