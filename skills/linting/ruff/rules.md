# Rule selection

**What it decides:** which rules run, and what one of them means.
Verified on ruff 0.16.9 (and 0.15.8 where marked), offline.

## Ask ruff

| Question | Command |
| --- | --- |
| what does `F841` mean, is its fix safe, which settings change it | `uv run --no-sync ruff rule F841` |
| every rule, machine-readable | `uv run --no-sync ruff rule --all --output-format json` (970 rules on 0.16.9) |
| the prefixes and their origin | `uv run --no-sync ruff linter` (`F Pyflakes`, `B flake8-bugbear`, `UP pyupgrade`, ...) |
| what a config key does and its default | `uv run --no-sync ruff config lint.select` |
| which rules are on for this file | `uv run --no-sync ruff check --show-settings <file>`, the `linter.rules.enabled` list |
| which rules fire most | `uv run --no-sync ruff check --statistics` |

A code that `ruff rule` does not know (`invalid value 'TCH001'`) was
renamed or removed; in a config, ruff remaps renamed codes with a
warning (`TCH003 has been remapped to TC003`).

## The default set changed in 0.16

With no `select` anywhere in the config:

| Version | Rules on | Which |
| --- | --- | --- |
| 0.15.8 | 59 | `E4`, `E7`, `E9`, `F` |
| 0.16.9 | 413 | 38 prefixes: `PYI` 47, `UP` 42, `F` 39, `RUF` 36, `PLE` 33, `B` 29, `SIM` 21, `PLW` 20, ... and single rules such as `I001`, `E722`, `BLE001`, `S110` |

On 0.16.9 the default no longer has `E401` or `E402`, but it has import
sorting (`I001`), `B006` and `UP045`. *Lab:* one file gave 1 finding on
0.15.8 and 4 on 0.16.9. `print` (`T201`) and `assert` (`S101`) are
still off by default.

So: **pin `select` in the project config.** Then an upgrade adds rules
only when someone decides it. Count before and after with
`--show-settings` and `--statistics`.

## Choosing rules

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]   # replaces the default set
ignore = ["E501"]                      # takes these back out
```

- `select` replaces the set; `extend-select` adds to it (to the
  defaults when there is no `select`).
- More specific prefixes win over less specific: `select = ["E"]` with
  `ignore = ["E5"]` drops `E501`; `ignore` wins when the same prefix is
  in both (`ruff config lint.select`).
- `select = ["ALL"]` turns on every stable rule, including pairs that
  contradict each other; ruff warns and drops one of each pair
  (`D203` and `D211`, `D212` and `D213`). Use it to explore, not as a
  project setting unless the team chose it.
- Never widen the selection inside another task; read the project's
  choice, including its comments on ignored rules.

## Preview

`--preview` (or `preview = true`) adds unstable rules and fixes. On
0.16.9 it also printed rule names instead of codes
(`unused-import: [*] ...`) unless `output-prefer-rule-codes = true`.
Match CI: use preview only if CI does.

## Rules that other skills rely on

| Rule | Name (0.16.9) | Owner of the underlying decision |
| --- | --- | --- |
| `N818` | error-suffix-on-exception-name | architecture (custom exceptions) |
| `TRY002`, `TRY003` | raise-vanilla-class, raise-vanilla-args | architecture |
| `B904` | raise-without-from-inside-except | architecture |
| `D` rules, `[tool.ruff.lint.pydocstyle] convention` | pydocstyle | documentation reads the convention; this skill owns the setting |
| `S101` | assert | pytest (tests assert); set `per-file-ignores` for `tests/**` here |
