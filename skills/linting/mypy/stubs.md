# Missing modules and missing types, offline

**What it decides:** the narrowest lasting setting that lets mypy check
code that imports something it cannot see or cannot type. Verified on
mypy 2.3.1 with a uv project and a path dependency.

## Which error is it?

| Error | Meaning | First check |
| --- | --- | --- |
| `Cannot find implementation or library stub for module named "x"  [import-not-found]` | mypy's environment does not have `x` | is mypy running in the project's environment? |
| `Skipping analyzing "x": module is installed, but missing library stubs or py.typed marker  [import-untyped]` | `x` is installed and has no types | is `x` ours (fix it there) or a third party (stub)? |
| `Library stubs not installed for "yaml"  [import-untyped]` with `note: Hint: "python3 -m pip install types-PyYAML"` | mypy knows a stub package exists for it | is that stub package in the mirror? |

*Lab:* a mypy installed elsewhere reported `import-not-found` for a
package the project had; `uv run --no-sync mypy` found it. Fix the
environment before any setting: run mypy through uv, or pass
`--python-executable .venv\Scripts\python.exe` (the navigation skill has
the environment probes). Whether an installed package ships `py.typed`
or stubs is the offline-docs skill's lookup.

## The options, narrowest lasting one first

For an internal package with no types (the lab's `legacy_utils`,
`def slugify(text)` with no annotations), under `strict = true`:

| Option | Result in the lab |
| --- | --- |
| add `py.typed` and annotations to the package itself, and reinstall it | the real fix; the import error went away. Needs the package's owner |
| a stub in the project: `stubs/legacy_utils/__init__.pyi` with `def slugify(text: str) -> str: ...`, and `mypy_path = "stubs"` in `[tool.mypy]` | `Success: no issues found`; the calls are typed |
| an override with `follow_untyped_imports = true` for `["legacy_utils", "legacy_utils.*"]` | import error gone; `no-untyped-call` and `no-any-return` at each use, because the functions have no annotations |
| an override with `ignore_missing_imports = true` for the same modules | import error gone; the module is `Any`, so `no-any-return` where its values are returned as typed |
| `ignore_missing_imports = true` in `[tool.mypy]` | hides every missing module in the project, now and later. **Never** |

A stub file is a Python file with signatures and `...` bodies. Type
only what the project uses, and say in the answer that it must follow
the package's changes.

## What does not work air gapped

- `pip install types-PyYAML`, `python3 -m pip install ...` (the hint
  mypy prints), and `mypy --install-types`, which installs with pip.
- A stub package can come from the internal mirror if it carries one:
  then it belongs in the dev group, added with `uv add --dev` only
  when the person asks (the packaging skill owns dependency groups).

## pyright

pyright did not complain about the untyped installed package at all
(it infers from the source); it reported only
`Import "x" could not be resolved (reportMissingImports)` when the
package was not in its environment (`pyright/install.md`).
