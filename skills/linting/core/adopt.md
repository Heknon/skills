# Bring a checker, or a stricter mode, to existing code

**Verdict you produce:** the config, the counts before and after, the
written ratchet, and the next step.

```
before:   mypy (defaults) 2 errors; mypy --strict 202 errors in 8 files
config:   strict = true; crm.legacy.* relaxed for untyped defs (pyproject.toml)
after:    2 errors, both real (listed); 0 in crm.api
ratchet:  8 legacy modules listed; a module leaves the list when it passes strict
ci:       uv run --no-sync mypy added to the lint job
```

Nobody fixes 200 functions in one change, and nobody should switch a
checker off to get green. The answer is a setting that is strict for
new code, tolerant for listed old code, and a list that only shrinks.

## 1. Measure

Count per module and per code before choosing anything. In PowerShell
(*lab, PowerShell 7.4*):

```powershell
$out = uv run --no-sync mypy --strict src
$out[-1]      # Found 202 errors in 8 files (checked 12 source files)
$out | Select-String -Pattern '^(src[^:]+):\d+: error' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } |
    Group-Object | Sort-Object Count -Descending | Format-Table Count, Name
$out | Select-String -Pattern '\[([a-z-]+)\]$' |
    ForEach-Object { $_.Matches[0].Groups[1].Value } |
    Group-Object | Format-Table Count, Name
```

Run it with the default settings too: in the lab sandbox the defaults
gave 2 errors (real bugs) and strict gave 202, of which 200 were
`no-untyped-def`. For ruff, `uv run --no-sync ruff check --statistics`
prints one line per rule with its count.

## 2. Configure: strict by default, old code listed

```toml
[tool.mypy]
strict = true
warn_unused_configs = true

# Legacy modules: checked, but untyped functions allowed.
# Remove a module from this list once `mypy --strict` passes on it.
[[tool.mypy.overrides]]
module = ["crm.legacy.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
check_untyped_defs = true
```

*Lab, mypy 2.3.1:* this gave 2 errors, the real ones, and new code in
`crm.api` stays strict. The alternative, listing new packages as strict,
does not work:

**`strict = true` inside `[[tool.mypy.overrides]]` turns strict on for
every module.** mypy calls its global strict switch for any section
that says `strict` and prints no warning (read in the installed mypy's
`config_parser.py`; *lab, 2.3.1 and 1.20.2*: an override for
`crm.api.*` with `strict = true` gave 203 errors, the legacy modules
included). Relax flags for old modules as above, or list the individual
flags `--strict` turns on (`mypy/strictness.md`) in the override for new
ones.

## 3. Deal with what is left

The errors left under the relaxed settings are usually real. List them,
and fix each one only if the fix does not change behaviour (an
annotation that was wrong); a fix that changes what the code returns is
the person's decision.

`ignore_errors = true` for a module switches every check off there,
bugs included. Use it only for generated code or code about to be
deleted, and name each module.

## 4. Write the ratchet down

In the config comment, or a short file the config points to: the listed
modules, their counts today, and the rule "a module leaves the list when
it passes, and nothing is added". The next change that touches a legacy
module is the moment to type it and remove it from the list.

## 5. Add the job

Add the same command to CI (`uv run --no-sync mypy`); set `files` or
pass the paths so CI and people check the same thing. The deployment
skill writes the job.

## Other checkers

- **ruff**: pin `select` explicitly before adopting, so upgrades do not
  add rules (`ruff/rules.md`). For a baseline, `ruff check --add-noqa`
  writes `# noqa: <codes>` on every failing line; `--add-noqa="legacy"`
  appended the reason (`# noqa: F401 legacy`). Use it only when the
  person asks for a baseline: it hides every finding it covers.
- **pyright**: `strict = ["src/app/new"]` makes chosen paths strict
  (`pyright/strictness.md`). basedpyright also has `--writebaseline`
  and `--baselinefile` (in its `--help`; not used in the lab).
