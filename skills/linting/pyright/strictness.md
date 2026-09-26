# pyright modes, strict paths and file comments

**What it decides:** how strict pyright is and for which files.
Verified on pyright 1.1.414 and basedpyright 1.40.1.

## Modes

`typeCheckingMode` takes `off`, `basic`, `standard` or `strict` in
pyright (any other value: `Config "typeCheckingMode" entry must contain
"off", "basic", "standard", or "strict".`). pyright's default is
`standard`. basedpyright adds `recommended` and `all`, and its default
is `recommended`.

On one sample file (an `arg-type` error, an operator error in an
unannotated function, a `bytearray` return, a method override with
another parameter type), with nothing else configured:

| Mode | pyright 1.1.414 | basedpyright 1.40.1 |
| --- | --- | --- |
| no mode set | 4 errors (as `standard`) | 4 errors, 6 warnings (as `recommended`) |
| `off` | 0 errors | 0 errors |
| `basic` | 3 errors (not the override) | 3 errors |
| `standard` | 4 errors | 4 errors |
| `recommended` | | 4 errors, 6 warnings (unknown and missing parameter types) |
| `strict` | 9 errors | 9 errors |
| `all` | | 10 errors |

Zed sets basedpyright to `standard` unless its settings say otherwise
(`core/zed.md`), so the panel is not basedpyright's CLI default.

## Strict for part of the project

```toml
[tool.pyright]
include = ["src"]
strict = ["src/app/new"]
```

*Lab:* only files under `src/app/new` got the strict rules. A file can
also opt in with a comment on its first lines:

```python
# pyright: strict
```

which worked in a folder not listed in `strict`. `# pyright: basic`
does the opposite: in a project set to `strict`, a file starting with it
got the `basic` count (3 errors instead of 9). A rule can be set on its own, at any
level: `reportUnnecessaryTypeIgnoreComment = "warning"`, or `"error"`,
`"none"`.

## Adopting

Like mypy (`core/adopt.md`): measure per file with `--outputjson`,
keep the project mode, list new paths under `strict`, and grow the list.
basedpyright can instead record today's findings with
`--writebaseline` and read them with `--baselinefile` (in its
`--help`; not used in the lab).
