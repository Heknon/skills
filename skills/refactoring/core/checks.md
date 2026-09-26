# Checks after each step

**Verdict you produce:** each check's summary line after the step,
against the baseline.

```
tests:      <pytest summary> (baseline <summary>)
ruff:       <line> ; new findings: <none | codes>
types:      mypy <line> ; pyright <line or not in project>
import-all: <import_all summary>
probe:      <identical | differs: <lines>>
names:      <no line lost or changed | <lines>, each explained>
verdict checks: <green | red: <check>>
```

Each check sees a different kind of miss. None sees them all, so all of
them run after every step, not once at the end.

## The checks, in order

```powershell
uv run --no-sync pytest -q
uv run --no-sync ruff check <folders CI checks>
uv run --no-sync mypy <folders CI checks>          # if the project has it
uv run --no-sync pyright <folders>                 # if the project has it
uv run --no-sync python <skill>/tools/import_all.py <package> --config pyproject.toml --config <each config file naming code> --scripts <scripts folder>
uv run --no-sync python .ledger/probe.py | Out-File -Encoding utf8 .ledger/probe-after.txt
git diff --no-index --exit-code .ledger/probe-before.txt .ledger/probe-after.txt
uv run --no-sync python <skill>/tools/public_names.py <modules> | Out-File -Encoding utf8 .ledger/names-after.txt
git diff --no-index .ledger/names-before.txt .ledger/names-after.txt
```

Green means: tests pass in the same number as the baseline, no new
finding from ruff or the type checker, import-all reports `0 failed`,
the probe is identical, and no public-names line was lost or changed
without an explanation (a line added is harmless; `tools/public-names.md`
says how to read the rest).

## What each check caught in the lab

Python 3.12.14, ruff 0.16.9 with `E`, `F`, `B`, mypy 2.3.1 without
options, pyright 1.1.414 in basic mode.

| Miss | pytest | ruff | mypy | pyright | import_all | public_names |
| --- | --- | --- | --- | --- | --- | --- |
| a call left with the old name in the same module | if a test runs it | `F821 Undefined name` | `name-defined` | `reportUndefinedVariable` | only if the module runs it at import | |
| the old name left in `__all__` | no | `F822 Undefined name ... in __all__` | no | `reportUnsupportedDunderAll` (warning) | no | |
| `from old import name` left in another module | if a test imports it | no | `attr-defined`: `Module "app.helpers" has no attribute "parse_date"` | `reportAttributeAccessIssue`: `"get_user" is unknown import symbol` | FAIL `ImportError: cannot import name` | the name's line is gone |
| `module.old()` inside a function with no annotations | if a test runs it | no | no (`--check-untyped-defs` finds it) | `reportAttributeAccessIssue` | no | |
| `obj.old()` on an untyped parameter | if a test runs it | no | no | no | no | |
| an import of a module that moved | if a test imports it | no | `import-not-found` | `reportMissingImports` | FAIL | |
| a keyword argument after a parameter rename | if a test passes it | no | `call-arg`: `Unexpected keyword argument` | `reportCallIssue`: `No parameter named` | no | the signature line changed |
| `mock.patch("pkg.mod.old")` in a test | `AttributeError: <module 'app.users' ...> does not have the attribute 'get_user'` | no | no | no | no | |
| a patch of the old place after a move | the patch misses: the real value comes through | no | no | no | no | |
| `getattr(obj, "old", None)` | no, if no test takes that path | no | no | no | no | |
| a dotted path in YAML, TOML or INI | no | no | no | no | FAIL with `--config` | |
| an entry point in `pyproject.toml` | no | no | no | no | FAIL with `--config pyproject.toml` | |
| a script outside the package | no | no | only if its folder is checked | only if its folder is checked | FAIL with `--scripts` | |
| a public name outside `__all__` not re-exported | no | no | no | no | no | the name's line is gone |
| a circular import made by a move | collection error | no | no | no | FAIL `partially initialized module` | |
| a shim written as a plain import | no | `F401 [*]` in a module: `--fix` deletes the shim | `--strict`: `does not explicitly export attribute` | no | | |

Read the table as: a green run of one check proves nothing about the
rows where it says no. The search in `core/every-reference.md` covers
what none of them sees (strings, docs, other repositories).

## Reading them

- **The finding's meaning** comes from the tool (linting's
  `core/read-finding.md`), never from memory.
- **mypy skips the bodies of functions without annotations** unless
  `check_untyped_defs` is set; in the lab `users.get_user(uid)` inside
  `def untyped_caller(uid):` passed mypy and failed pyright. When the
  project has only mypy, list the untyped callers the search found under
  *Not checked*.
- **ruff's `F401` on a shim:** in `__init__.py` it is reported with no
  fix (`consider removing, adding to __all__, or using a redundant
  alias`); in any other module it is `[*]`, a safe fix, and
  `ruff check --fix` removes the shim. Write re-exports as
  `from new import name as name` or list them in `__all__`
  (`core/public-surface.md`).
- **A new type finding about old behaviour.** Typing a value the old
  code left untyped can show a bug it always had: in recipe L3, mypy
  reported `union-attr` for a missing user that was a 500 before and
  after the step. Show with the probe that behaviour is the same, report
  the finding under *Findings*, and never silence it; the fix is its own
  commit.
- **Formatting is not a check of the step.** Run `ruff format --check`
  only if CI does, and only on the files the step touched.

## Never

- Never skip a check because an earlier one was green.
- Never call a step green with fewer tests passing than the baseline, or
  with tests deselected, skipped or marked to fail.
- Never run the checks on a different interpreter or tool version from
  the baseline.
