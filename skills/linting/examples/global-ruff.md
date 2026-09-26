# Worked example: four errors here, one in CI

Kinds: Match CI, Fix. Outputs from a lab run (Linux; the person's
machine was Windows, so their commands are shown in PowerShell).

## The ask

> I ran ruff check and got 4 errors, but CI only complains about one.
> Fix everything so we're clean.

The person's output started `PS C:\work\billing> ruff check .` and
listed `F401`, `UP045`, `B006` and `BLE001`. The CI log:

```
$ uv sync --locked
 + ruff==0.15.8
$ uv run --no-sync ruff check .
F401 [*] `os` imported but unused
 --> src/billing/charges.py:2:8
Found 1 error.
```

## Steps

1. **Versions before any edit** (`core/run-like-ci.md`):
   ```
   > ruff --version
   ruff 0.16.9
   > uv run --no-sync ruff --version
   ruff 0.15.8
   > uv tree --frozen --only-group dev --depth 1
   billing v0.1.0
   └── ruff v0.15.8 (group: dev)
   ```
   The person ran a global ruff; the project and CI pin 0.15.8.
2. **Why the counts differ.** The config has no `select`. Counting
   `linter.rules.enabled` in `ruff check --show-settings
   src/billing/charges.py`: 413 rules on 0.16.9, 59 on 0.15.8
   (`ruff/rules.md`). `UP045`, `B006` and `BLE001` are not on in CI.
3. **Fix what CI reports.** `F401`: `os` is unused in
   `src/billing/charges.py` and is not a re-export; removed the line.
4. **Run CI's command.**
   ```
   > uv run --no-sync ruff check .
   All checks passed!
   ```
5. **Left alone, on purpose.** The other three findings would change
   code CI never asked about; `B006`'s and `UP045`'s fixes are changes of
   behaviour or style for the team to decide. The global 0.16.9 still
   reports them: `Found 3 errors.`

## The answer

```
## Result
CI's one finding is fixed: removed the unused `import os` from
src/billing/charges.py. The other three came from a different ruff:
yours on PATH is 0.16.9, the project and CI use 0.15.8 (uv.lock). With
no `select` in the config, 0.16.9 turns on 413 rules by default and
0.15.8 turns on 59, so UP045, B006 and BLE001 are not checked in CI.
I did not change them. Before anyone upgrades ruff, I suggest pinning
`select` in [tool.ruff.lint] so the upgrade does not change the rules;
I can do that as a separate change. Run ruff as `uv run --no-sync ruff`
to get the project's version.

## Checked
- ruff 0.15.8 (uv run --no-sync ruff --version, uv tree); global 0.16.9.
- uv run --no-sync ruff check . : All checks passed!

## Not checked
- The CI pipeline itself; I ran the same command locally.
```
