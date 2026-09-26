# mypy strictness and per-module settings

**What it decides:** how strict mypy is, for which modules, and where
that is written. Verified on mypy 2.3.1 (1.20.2 where marked).

## What `strict = true` turns on

From `mypy --help` on 2.3.1: `--disallow-any-generics`,
`--disallow-subclassing-any`, `--disallow-untyped-calls`,
`--disallow-untyped-defs`, `--disallow-incomplete-defs`,
`--check-untyped-defs`, `--disallow-untyped-decorators`,
`--warn-redundant-casts`, `--warn-unused-ignores`, `--warn-return-any`,
`--no-implicit-reexport`, `--strict-equality`, `--extra-checks`.
On 1.20.2 the list also had `--strict-bytes`, which 2.x turns on by
default (`mypy/versions.md`).

Without strict, mypy does not check inside unannotated functions and
treats their calls as `Any` (`mypy/errors.md`).

## Where settings go

```toml
[tool.mypy]
strict = true
warn_unused_configs = true
files = ["src"]

[[tool.mypy.overrides]]
module = ["crm.legacy.*", "crm.scripts"]
disallow_untyped_defs = false
check_untyped_defs = true
```

The same in `mypy.ini`: a `[mypy]` section, and `[mypy-crm.legacy.*]`
sections for overrides, with `True`/`False`.

- `module` takes a list; `pkg.*` matches the package and its submodules
  (*lab:* `["legacy_utils.*"]` also covered `import legacy_utils`).
- Only per-module options work in an override. A global one is reported
  and ignored: `pyproject.toml: [module = "crm.api.*"]: Per-module
  sections should only specify per-module flags (python_version)`.
  The per-module options (from `mypy.options.PER_MODULE_OPTIONS`)
  include `check_untyped_defs`, `disallow_untyped_defs`,
  `disallow_incomplete_defs`, `disallow_untyped_calls`,
  `disallow_any_generics`, `warn_return_any`, `warn_unused_ignores`,
  `strict_equality`, `extra_checks`, `ignore_errors`,
  `ignore_missing_imports`, `follow_untyped_imports`, `follow_imports`,
  `implicit_reexport`, `enable_error_code`, `disable_error_code`.
- **`strict` is not one of them, and is not reported.** In an override
  it turns strict on for every module (*lab, 2.3.1 and 1.20.2*: 203
  errors instead of 1). To make only new code strict, set strict
  globally and relax the old modules, or put the individual flags above
  in the new modules' override.
- `warn_unused_configs = true` reports override patterns that matched
  nothing: `pyproject.toml: note: unused section(s): module =
  ['unused_thing.*']`. Use it whenever you write overrides.

## Checking the effect

Count before and after (`core/adopt.md`). For one module, pass its file
(`uv run --no-sync mypy src/crm/api/contacts.py`); `-m crm.api.contacts`
failed in a `src/` layout with `Cannot find module`. A setting
that seems to do nothing is usually in a file mypy did not read
(`core/config-files.md`) or under a pattern that matched nothing
(`warn_unused_configs`).

## Error codes, project-wide

```toml
[tool.mypy]
enable_error_code = ["ignore-without-code", "possibly-undefined"]
disable_error_code = ["import-untyped"]   # hides every untyped import; scope it with an override instead
```

Prefer an override for one package over a global
`disable_error_code`: the global form silences every future case too.
