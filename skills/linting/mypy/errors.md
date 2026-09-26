# Reading mypy's output

**What it decides:** what a mypy error says, and how to get more from
mypy about it. Verified on mypy 2.3.1; 1.20.2 printed the same lines.

## The shape

```
src/app/core.py:10: error: Argument 1 to "greet" has incompatible type "str | None"; expected "str"  [arg-type]
src/app/core.py:11: note: Revealed type is "str | None"
Found 3 errors in 1 file (checked 2 source files)
```

- `path:line: error: message  [code]`. The code is always shown in 2.x
  (`--hide-error-codes` hides it).
- `note:` lines add to the error above; they are not counted.
- The last line: `Success: no issues found in N source files` (exit 0),
  `Found N errors in M files (checked K source files)` (exit 1), or a
  fatal problem such as `Cannot read file 'nosuch.py'` with `errors
  prevented further checking` (exit 2).
- More detail: `--show-column-numbers`, `--show-error-end`, and
  `--pretty`, which prints the source line with `^~~~` under the
  expression.

## Codes seen in the lab

| Code | Message starts | Usual cause |
| --- | --- | --- |
| `arg-type` | `Argument 1 to "f" has incompatible type` | passing `X \| None` where `X` is expected |
| `return-value` | `Incompatible return value type (got "float", expected "int")` | the annotation or the value is wrong |
| `assignment` | `Incompatible types in assignment` | a variable reused with another type |
| `call-arg` | `Unexpected keyword argument "display_name" for "User"` | a wrong name, or a model mypy reads without its plugin (`mypy/pydantic.md`) |
| `union-attr` | `Item "None" of "Any \| None" has no attribute "strip"` | `None` not handled |
| `attr-defined` | `"Settings" has no attribute "page_size"` | an attribute added at runtime |
| `import-not-found` | `Cannot find implementation or library stub for module named "x"` | not installed in the environment mypy uses (`mypy/stubs.md`) |
| `import-untyped` | `module is installed, but missing library stubs or py.typed marker` | a package with no types (`mypy/stubs.md`) |
| `no-untyped-def` | `Function is missing a type annotation` | strict mode on an unannotated function |
| `no-untyped-call` | `Call to untyped function "slug" in typed context` | strict mode calling unannotated code |
| `no-any-return` | `Returning Any from function declared to return "str"` | a value from untyped code returned as typed |
| `unused-ignore` | `Unused "type: ignore" comment` | `warn_unused_ignores` found a stale ignore |
| `ignore-without-code` | `"type: ignore" comment without error code (consider "type: ignore[arg-type]" instead)` | enabled with `enable_error_code` |

A code's description, offline:
`uv run --no-sync python -c "from mypy.errorcodes import error_codes as e; print(e['no-any-return'].description)"`.
The same registry says which codes are off by default (`deprecated`,
`explicit-override`, `ignore-without-code`, `possibly-undefined`,
`redundant-expr`, `truthy-bool`, `unused-awaitable`, `unused-ignore` and
others); turn one on with `enable_error_code = ["..."]` or
`--enable-error-code`.

## What mypy does not check by default

The body of a function with no annotations is not checked: *lab*, a
`None.strip()` crash and a missing attribute in unannotated functions
gave `Success`; with `--check-untyped-defs` both were reported
(`union-attr`, `attr-defined`). pyright checks those bodies by default,
which is one reason the two disagree (`core/zed.md`).

## Asking mypy for types

- `reveal_type(expr)` prints `note: Revealed type is "..."`.
- `reveal_locals()` prints every local variable and its type
  (`note: Revealed local types are:` then `a: str` lines).

Neither needs an import for mypy, and both fail at runtime without one,
so put them in a scratch file or remove them before running the code.
The navigation skill has the probe-file procedure.

## Which Python and which packages

mypy checks for the Python version it runs under unless
`python_version` is set, and finds packages in the environment it is
installed in unless `--python-executable` points elsewhere. *Lab:* a
mypy from another environment reported `import-not-found` for a package
that `uv run --no-sync mypy` found. Run it through uv from the project.
