# pyright configuration

**What it decides:** where pyright's settings go and which environment
it checks against. Verified on pyright 1.1.414. Which file wins is in
`core/config-files.md`: `pyrightconfig.json` over `[tool.pyright]`.

## The same settings in both forms

```toml
# pyproject.toml
[tool.pyright]
include = ["src"]
strict = ["src/app/new"]
typeCheckingMode = "standard"
pythonVersion = "3.12"
venvPath = "."
venv = ".venv"
reportUnnecessaryTypeIgnoreComment = "warning"
```

```json
{
  "include": ["src"],
  "strict": ["src/app/new"],
  "typeCheckingMode": "standard",
  "pythonVersion": "3.12",
  "venvPath": ".",
  "venv": ".venv",
  "reportUnnecessaryTypeIgnoreComment": "warning"
}
```

basedpyright read `[tool.basedpyright]` in the lab (`typeCheckingMode` there
took effect).

## Keys checked in the lab

| Key | Effect seen |
| --- | --- |
| `include` | the folders checked when no files are given |
| `strict` | paths that get strict mode (`pyright/strictness.md`) |
| `typeCheckingMode` | `off`, `basic`, `standard`, `strict` |
| `pythonVersion` | `--verbose` printed `Python version: 3.11` after setting `"3.11"` |
| `venvPath` + `venv` | the project's `.venv` used even when pyright was not started through it; a package missing before was found |
| `report<Rule>` | `"error"`, `"warning"`, `"none"` for one rule |
| `enableTypeIgnoreComments = false` | `# type: ignore` stopped silencing pyright (the error came back); `# pyright: ignore[...]` still works |

An unknown key is reported (`Config contains unrecognized setting`),
and pyright still runs.

## Which environment pyright uses

pyright uses the `python` on `PATH` unless told otherwise. `--verbose`
prints `Search paths:` with the `site-packages` it used.

| Start | What it saw in the lab |
| --- | --- |
| `pyright src` with another Python on `PATH` | `Import "legacy_utils" could not be resolved (reportMissingImports)` |
| `uv run --no-sync pyright src` (pyright in the project's dev group) | the project's packages |
| `venvPath` and `venv` in the config | the project's packages, from any start |
| `--pythonpath .venv\Scripts\python.exe` | the navigation skill's probe form |

For CI and hooks, run pyright through uv like the other tools; the
`venvPath`/`venv` pair helps editors and people who start it by hand.
