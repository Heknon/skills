# Recipes

Complete projects that were built, installed and run. Copy one whole and
change only what its top comment names. Every recipe's `pyproject.toml`
points at `https://pypi-mirror.example.com/simple`: put the mirror's URL
there.

| Recipe | Shows | Backend |
| --- | --- | --- |
| `src-hatchling/` | the default for a new project: src layout, a console script, a template read with `importlib.resources`, `py.typed`, an extra, a `dev` group | hatchling 1.32.4 |
| `flat-setuptools/` | an existing flat project: `packages.find include`, `package-data`, a version read from `__version__` | setuptools 84.0.0 |
| `uv-build/` | a pure-Python library on uv's backend, data inside the package | uv_build 0.12.19 |
| `workspace/` | a virtual root, a library and a service as namespace packages (`acme.core`, `acme.api`), a bounded sibling with a workspace source | hatchling 1.32.4 |
| `independent-projects/` | two projects in one repository with their own locks, one using the other by path | hatchling 1.32.4 |
| `internal-index/` | the mirror as default, an explicit internal index with a publish URL, a source line per internal package | hatchling 1.32.4 |
| `wheelhouse/` | `fetch-wheels.sh` for the connected side, the check and the offline install (`README.md`) | pip 26.2.1 |
| `tools/inspect_dist.py` | lists a wheel's or sdist's metadata, backend, entry points and files; `--against` finds missing files | standard library |

## How each was checked

uv 0.12.19, Python 3.12, a local index standing in for the mirror, the
network cut (a network namespace with only loopback) for every step after
the first lock. For each recipe:

1. `uv lock`, then the tests: `uv run pytest` (workspace: `uv run
   --package <member> pytest <folder>`).
2. `uv build` (the sdist, then the wheel from it; workspace: `uv build
   --all-packages`).
3. `inspect_dist.py "dist/*" --against <package folder>` on the sdist and
   the wheel: `every source file is in the distribution`, and the
   `built by:` line.
4. A fresh venv, the wheel installed by its path with `--offline`, the
   package imported from outside the checkout, each console script run.

Results:

| Recipe | Lab output |
| --- | --- |
| `src-hatchling/` | `1 passed`; `built by: hatchling 1.32.4`; `acme-report 2026-08 --total 1200.5` printed `Report 2026-08: 1200.50` |
| `flat-setuptools/` | `1 passed`; `built by: setuptools (84.0.0)`; `ledger USD 100` printed `USD 100.00 -> EUR 93.00`. Without `package-data`, `data/accounts.json` was `MISSING` from both; `py.typed` shipped anyway |
| `uv-build/` | `1 passed`; `built by: uv 0.12.19`; `acme-tax DE 100` printed `DE 100.00 -> 119.00` |
| `workspace/` | one lock (`Resolved 9 packages`); `uv sync --package acme-api` installed acme-api, acme-core, click and the member's dev tools; `Requires-Dist: acme-core<2,>=1.2`; both wheels in one venv: `acme-api 1.10 2.20` printed `total 3.30`, and `import acme.core, acme.api` worked |
| `independent-projects/` | a `uv.lock` in each folder; billing's tests `1 passed`; both wheels installed together with pydantic 1.10.26 |
| `internal-index/` | acme-report locked from the internal index (credentials from `UV_INDEX_INTERNAL_*`), click from the mirror; `uv publish --index internal` uploaded to a local test index, and a second run printed `already exists, skipping` |
| `wheelhouse/` | see its `README.md` |

Nothing was ever uploaded to a public index.
