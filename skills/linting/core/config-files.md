# Which file each tool reads

**Verdict you produce:** the file each tool read, shown by the tool, and
the file you changed.

```
ruff:    Settings path: .../ruff.toml         (ruff check --show-settings <file>)
mypy:    Config File: .../pyproject.toml       (mypy -v)
pyright: Loading pyproject.toml file at ...   (pyright --verbose)
edited:  ruff.toml, [lint.per-file-ignores]
```

Never edit a config file before asking the tool which one it reads.
Two files for one tool is common, and the loser is ignored without a
warning.

## ruff

- In one folder: `.ruff.toml` wins over `ruff.toml`, which wins over
  `pyproject.toml` (*lab, 0.16.9*: with both `ruff.toml` and
  `[tool.ruff]`, the `per-file-ignores` in `pyproject.toml` had no
  effect and nothing warned).
- A `pyproject.toml` without a `[tool.ruff]` table is not a config file;
  ruff looks further up.
- Each file uses the closest config file above it. A config in a
  subfolder replaces the parent's completely; it does not merge. *Lab:*
  a `tests/ruff.toml` with only `line-length = 60` switched the
  parent's `S` rules off for `tests/`. To inherit, start the file with
  `extend = "../ruff.toml"` (or `"../pyproject.toml"`).
- `target-version`, when not set, comes from `requires-python` in the
  nearest `pyproject.toml`, even when the settings are in `ruff.toml`
  (`ruff check -v` printed ``Derived `target-version` from
  `requires-python`: Py312``).
- A misspelt key stops ruff: `ruff failed` ... `TOML parse error`.
- Proof: `uv run --no-sync ruff check --show-settings <file>` prints
  `Settings path:` and every resolved setting (`linter.rules.enabled`,
  `linter.per_file_ignores`, `linter.line_length`). `--isolated` ignores
  all config files; `--config "line-length = 100"` overrides one key.

## mypy

- mypy looks in the **current folder**, then each parent, for
  `mypy.ini`, `.mypy.ini`, `pyproject.toml` with `[tool.mypy]`, and
  `setup.cfg` with `[mypy]`, in that order; it stops at a folder with
  `.git` or `.hg`, and then tries `~/.config/mypy/config` and
  `~/.mypy.ini` (read in the installed mypy's `config_parser.py`, 2.3.1
  and 1.20.2).
- So the config depends on where mypy is started, not on the files it
  checks. *Lab:* in a uv workspace, `mypy services/api/src` from the
  root printed `Config File: Default` and missed the member's
  `strict = true`; from `services/api` it found it. Use
  `--config-file services/api/pyproject.toml` to be explicit.
- *Lab:* with `mypy.ini` and `[tool.mypy]` both present, `mypy.ini`
  won and the `pyproject.toml` settings had no effect.
- A misspelt key is reported and skipped: `pyproject.toml: [mypy]:
  Unrecognized option: strcit = True`, and the run goes on.
- Proof: `uv run --no-sync mypy -v src 2>&1 | Select-String "Config File"`.
  `warn_unused_configs = true` reports override sections that matched
  no module: `pyproject.toml: note: unused section(s): module =
  ['unused_thing.*']`.

## pyright and basedpyright

- `pyrightconfig.json` wins over `[tool.pyright]` in `pyproject.toml`
  (*lab*: settings in the `pyproject.toml` table stopped applying when
  the JSON file appeared). basedpyright also reads
  `[tool.basedpyright]`.
- Run from a subfolder, pyright found the `pyproject.toml` above it.
- An unknown key prints `Config contains unrecognized setting
  "reportUnknownThing".`; an unknown mode prints `Config
  "typeCheckingMode" entry must contain "off", "basic", "standard", or
  "strict".`
- Proof: `uv run --no-sync pyright --verbose` prints `Loading
  configuration file at ...` or `Loading pyproject.toml file at ...`,
  then the Python version and `Search paths:`. `-p <file or folder>`
  chooses the config.

## Who owns which table

This skill owns `[tool.ruff]`, `[tool.mypy]`, `[tool.pydantic-mypy]`,
`[tool.pyright]`, `[tool.basedpyright]`, `ruff.toml`, `mypy.ini`,
`pyrightconfig.json` and `.pre-commit-config.yaml`, test settings in
them included (such as `per-file-ignores` for `tests/**`). `[project]`,
dependency groups and `[tool.uv]` are the packaging skill's;
`[tool.pytest]` is the pytest skill's.
