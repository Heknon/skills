# Verify: the wheel in a clean venv, offline, imported, its scripts run

**Verdict you produce:** for the change you made, the checks that ran and
their verdict lines. Nothing is done until they ran, or the answer says
why one could not.

```
built:    uv build -> "Successfully built dist/<sdist>", "Successfully built dist/<wheel>"
listed:   inspect_dist.py "dist\*" --against <folder> -> "every source file is in the distribution" (both)
metadata: Version <x.y.z>, Requires-Dist <as intended>
venv:     fresh, outside the checkout; the wheel installed by its path, --offline
imported: <import_name> from <venv>\Lib\site-packages\..., not from the checkout
ran:      <each console script> <args> -> <output>, exit 0
tests:    <optional: the test suite against the installed wheel> -> "<n> passed"
lock:     uv lock --check -> passes (when dependencies changed)
```

## Steps (PowerShell)

```
uv build --clear
uv run --no-project python <skill>\recipes\tools\inspect_dist.py "dist\*" --against src\acme_report

$venv = Join-Path ([System.IO.Path]::GetTempPath()) "verify-acme-report"
uv venv $venv --python 3.12 --clear
uv pip install --python "$venv\Scripts\python.exe" --offline dist\acme_report-1.2.0-py3-none-any.whl
Push-Location ([System.IO.Path]::GetTempPath())
& "$venv\Scripts\python.exe" -c "import acme_report; print(acme_report.__file__)"
& "$venv\Scripts\acme-report.exe" 2026-08 --total 1200.5
Pop-Location
```

Lab: these ran in PowerShell 7.5 on Linux, with `bin/python` and
`bin/acme-report` in place of the `Scripts\...exe` paths (not run on
Windows). Output: `.../site-packages/acme_report/__init__.py` and
`Report 2026-08: 1200.50`.

Why each part:

- **By its path.** `uv pip install --find-links dist acme-report`
  installed an older build of the same version from uv's cache after a
  rebuild (lab). The path always installs the file you built.
- **A fresh venv** (`--clear`): no editable install and no leftovers.
- **Outside the checkout** (`Push-Location` to the temp folder): Python
  puts the current folder on `sys.path`, so a flat-layout package in the
  checkout would be imported instead of the installed one.
- **`--offline`**: dependencies come from uv's cache of the mirror; if one
  is missing, the error says so, instead of reaching for a network.
  Without a cache, drop `--offline` and let it use the mirror.
- **The script itself**, not `python -m`: the console script is what
  users run (`core/entry-points.md`).

## The tests against the wheel

```
uv run --isolated --no-project --with dist\rates-2.0.0-py3-none-any.whl --with pytest pytest tests
```

Lab: with the JSON file missing from the wheel this gave `2 failed`,
while `uv run pytest` in the project gave `2 passed`; after the fix, `2
passed`. With src layout the tests import the installed package. With a
flat layout the checkout's package is on `sys.path` (pytest's rootdir),
so this check proves less: rely on the import from outside the checkout.

## Other checks

| Changed | Check | Verdict line |
| --- | --- | --- |
| dependencies | `uv lock --check` | exit 0 |
| the index or a source | `Select-String -Path uv.lock -Pattern 'registry = '` | every package from the index you intended |
| a workspace member's bounds | `uv build --all-packages`, then `uv pip install --dry-run --find-links dist <member>` into a scratch venv | resolves (`core/member-release.md`) |
| a wheelhouse | `uv pip compile ... --python-platform <target> --no-index --find-links wheelhouse` | resolves (`core/across-the-gap.md`) |
| a release | `uv publish --index <name> --dry-run --trusted-publishing never` | `Checking <n> files against <url>` |

## Never

- Never say "ready" or "fixed" from `uv run pytest` alone: it runs
  against the editable install, which reads the source tree.
- Never verify with a wheel you did not build in this task, or with the
  wrong file from a `dist\` that holds several versions.
