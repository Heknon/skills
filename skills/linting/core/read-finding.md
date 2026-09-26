# From an output line to its meaning

**Verdict you produce:** the finding, what its code means according to
the tool, and why this line triggers it.

```
finding:  src/app/report.py:10:5: F841 Local variable `skipped` is assigned to but never used
means:    unused-variable (F841), from `ruff rule F841`
cause:    `skipped = 0` is never read after line 10
next:     fix | configure | suppress, and why (core/decide.md)
```

## 1. Split the line

| Tool | Shape (lab, one line of each) |
| --- | --- |
| ruff, `--output-format concise` | ``src/app/report.py:2:8: F401 [*] `os` imported but unused`` |
| ruff, default (`full`) | `F401 [*] ...` then ` --> src/app/report.py:2:8`, the source lines, and a `help:` line |
| mypy | `src/app/core.py:10: error: Argument 1 to "greet" has incompatible type "str \| None"; expected "str"  [arg-type]` |
| pyright | `src/app/core.py:10:17 - error: Argument of type "str \| None" cannot be assigned ... (reportArgumentType)` |
| basedpyright | the same as pyright; its summary line says `notes` where pyright says `informations` |

- `[*]` after a ruff code means `--fix` can apply a fix; no mark means
  there is none or it is unsafe (`ruff/fixes.md`).
- mypy's `note:` lines belong to the error above them and are not
  counted. Read them: `Error code "arg-type" not covered by
  "type: ignore[assignment]" comment` says exactly what is wrong.
- pyright's indented lines under an error explain it step by step; the
  rule name is at the end of the last one.
- pyright's `--outputjson` counts lines from 0; its text output and the
  other tools count from 1.

## 2. Look the code up in the tool, not in memory

| Tool | Offline source |
| --- | --- |
| ruff | `uv run --no-sync ruff rule F841`: what it does, why, the fix and whether it is safe, and the settings that change it. `ruff linter` lists the prefixes. |
| mypy | `uv run --no-sync python -c "from mypy.errorcodes import error_codes as e; print(e['arg-type'].description)"` prints `Check argument types in calls`; the message itself names both types. |
| pyright | the rule name and the message; `--verbose` for where imports were looked for |

Rule codes move between versions. On ruff 0.16.9, `ruff rule TCH001`
failed with `invalid value 'TCH001'`, while `--extend-select TCH003`
still worked with `warning: TCH003 has been remapped to TC003`. A code
from a blog post, an old config or your memory may be one of these:
look it up in the installed version.

## 3. Find why this line triggers it

Read the line and the ones the message names. For type errors, ask the
checker for the types involved instead of guessing: `reveal_type(x)` in
a scratch file for mypy or pyright (the navigation skill has the probe),
or `reveal_locals()` for mypy, which printed each local and its type in
the lab. Delete the probe afterwards.

Ask:

1. **Is the rule on in CI's config?** A finding from `--select ALL`,
   another version, or the editor panel may not exist in CI
   (`core/run-like-ci.md`, `core/zed.md`).
2. **Is the finding true for this line?** Most are. The checker can be
   wrong where it cannot see what runs: a plugin not loaded
   (`mypy/pydantic.md`), dynamic attributes, a missing stub.
3. **Does it point at a bug?** In the lab, basedpyright's
   `"strip" is not a known attribute of "None"` in a function mypy did
   not check was a real crash: `feed_title([])` raised `AttributeError`.
   Run the case the finding describes when you can.

Then go to `core/decide.md`.
