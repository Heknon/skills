# Fixes, safe and unsafe

**What it decides:** which of ruff's fixes to apply, and how to see them
first. Verified on ruff 0.16.9.

## Reading the markers

```
a.py:1:8: F401 [*] `os` imported but unused
a.py:5:12: RUF015 Prefer `next(iter(rows))` over single element slice
Found 3 errors.
[*] 1 fixable with the `--fix` option (2 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

- `[*]`: a safe fix; `--fix` applies it.
- No mark: no fix, or an unsafe one. The last line counts the unsafe
  ones as "hidden fixes".
- `ruff rule <CODE>` says `Fix is always available`, `sometimes
  available` or `not available`, and its `## Fix safety` section says
  when and why a fix is unsafe.

## See before you apply

```
uv run --no-sync ruff check --diff <paths>                  # safe fixes as a diff; writes nothing
uv run --no-sync ruff check --diff --unsafe-fixes <paths>   # the unsafe ones too
uv run --no-sync ruff check --fix --show-fixes <paths>      # apply safe fixes, list what changed
```

`--diff` exits 1 when it has a diff to show and prints `Would fix N
errors (M additional fixes available with --unsafe-fixes)`. After
`--fix`, the summary says `Found 3 errors (1 fixed, 2 remaining)`.

## Unsafe fixes seen in the lab

| Rule | What the fix does | How it changed behaviour |
| --- | --- | --- |
| `RUF015` | `list(rows)[0]` becomes `next(iter(rows))` | an empty input raises `StopIteration`, not `IndexError`; two tests that expected `IndexError` failed |
| `B006` | `bucket=[]` becomes `bucket=None` plus `if bucket is None: bucket = []` | code that relied on the shared list (a cache) loses it |
| `F841` | removes the unused assignment | unsafe only because comments on it are dropped; the value's side effects stay (`int(x)` is kept) |
| `F401` in `__init__.py` | none in stable; in preview, an alias or `__all__` entry for first-party imports, removal (unsafe) for others | removing a re-export breaks `from package import name` |
| `UP045` | `Optional[X]` becomes `X \| None` | unsafe below Python 3.10, where libraries that read annotations at runtime (pydantic) fail |

Procedure for an unsafe fix:

1. Read its diff (`--diff --unsafe-fixes`) and its `## Fix safety`.
2. Decide whether the difference matters here: who catches the old
   exception, who relies on the old value.
3. Apply it by hand or with `--fix --unsafe-fixes` on that file and
   `--select <CODE>`, never over the repository.
4. Run the tests. If none cover the case, say so.

If the fix is wrong for this code, write the change yourself (for
`RUF015` a loop that returns the first row and raises `IndexError`
passed both ruff and the tests) or suppress the line with a reason.

## Settings

| Key (under `[tool.ruff.lint]`) | Does |
| --- | --- |
| `fixable`, `unfixable` | which rules `--fix` may touch |
| `extend-safe-fixes` | treat these rules' unsafe fixes as safe |
| `extend-unsafe-fixes` | treat these rules' safe fixes as unsafe |

Changing them changes what every `--fix` in the team does; it is a
Configure task, not part of a fix.

## Never

- Never `--fix --unsafe-fixes` over a folder you have not read the diff
  of.
- Never let `--fix` run over files outside the task (`core/in-scope.md`).
