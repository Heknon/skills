# Units and ties: the signs and the searches

Reference for `core/monorepo.md`. Every search here was run with git
2.43 and PowerShell 7.5.3 (for Linux; not run on Windows) on the lab
repository in `recipes/untangle/before/`, and the outputs quoted are
from there. Run them from the repository root.

First run the map. It does all of this at once, prints file:line for
every finding, and changes nothing:

```
uv run --no-project python <skill>\recipes\tools\map_units.py .
```

Then confirm each finding you rely on with its search below, and quote
that search's output in the answer. The map cannot see code built or
run from outside the repository, or a module name built at run time
(`importlib.import_module(name)`).

## A unit and its signs

A unit is anything that builds, runs or deploys on its own. The word
"monorepo" is not evidence; these are.

| Unit | Signs |
| --- | --- |
| a project | its own `pyproject.toml` (or `setup.py`, `setup.cfg`) |
| a program with no project | a `requirements*.txt`, a `__main__.py`, a file with a main guard, its own Dockerfile, a CI job that names its folder |
| a package deployed on its own inside one project | its own `[project.scripts]` entry, or its own Dockerfile that runs it |
| shared code | a folder of Python with none of the signs above that other units import |

A subfolder of one import package (`src/acme_reports/loaders/`) with no
sign of its own is not a unit: it is part of its project, whatever the
person calls the repository. A tests folder is never a unit.

```
git ls-files -- "*pyproject.toml" "*setup.py" "*setup.cfg" "*requirements*.txt" "*Dockerfile*" "*Containerfile*" "*__main__.py"
git grep -l -E "^if __name__ == .__main__.:"
git grep -n -A4 -F "[project.scripts]" -- "*pyproject.toml"
git grep -n -E "^(CMD|ENTRYPOINT)" -- "*Dockerfile*"
git grep -n -E "(api|worker|common)/" -- .gitlab-ci.yml
```

The last line takes the folder names found so far. Lab output:

```
$ git ls-files -- "*pyproject.toml" "*requirements*.txt" "*Dockerfile*" "*__main__.py" ".gitlab-ci.yml"
.gitlab-ci.yml
api/Dockerfile
requirements.txt
worker/Dockerfile
worker/__main__.py
$ git grep -l -E "^if __name__ == .__main__.:"
api/main.py
$ git grep -n -E "(api|worker|common)/" -- .gitlab-ci.yml
.gitlab-ci.yml:11:    - pytest api/tests
.gitlab-ci.yml:15:    - pytest worker/tests
.gitlab-ci.yml:19:    - buildah bud -f api/Dockerfile -t acme-api .
.gitlab-ci.yml:23:    - buildah bud -f worker/Dockerfile -t acme-worker .
```

## Ties between units

| Tie | What it looks like | Search |
| --- | --- | --- |
| an import across units | `from common.money import fmt` in `api/` | 1 |
| a path hack | `sys.path.insert(...)`, `sys.path.append(...)`, `site.addsitedir(...)` | 2 |
| `PYTHONPATH` | set in CI, a Dockerfile, `.env`, a README, a script | 3, 4 |
| a path dependency | `{ path = "../core" }` in `[tool.uv.sources]`; `-e ./core` or `file:` in a requirements file | 5 |
| a uv workspace | `[tool.uv.workspace]` in a `pyproject.toml` | 6 |
| a copy | the same module in two units | next section |
| a shared requirements file | one `requirements.txt` read by several Dockerfiles or jobs | 7 |
| shared config | one `.env` or settings file, or one variable name, read by several units | 4, 8 |

```
# 1. once per unit, with its import name; the pathspec leaves the unit itself out
git grep -n -E "^\s*(from|import)\s+common\b" -- ":!common/"
# 2.
git grep -n -E "sys\.path\.(insert|append)|site\.addsitedir"
# 3.
git grep -n PYTHONPATH
# 4. .env files are often in .gitignore, where git grep does not look
Get-ChildItem -Recurse -Force -File -Filter ".env*" | Where-Object FullName -notmatch "[\\/]\.venv[\\/]" | Select-String PYTHONPATH
# 5.
git grep -n -E "path\s*=|workspace\s*=" -- "*pyproject.toml"
git grep -n -E "^\s*(-e\s+)?\.\.?/|file:" -- "*requirements*.txt"
# 6.
git grep -n -F "[tool.uv.workspace]" -- "*pyproject.toml"
# 7.
git grep -n requirements -- "*Dockerfile*" .gitlab-ci.yml
# 8.
git grep -n -E "os\.environ|getenv"
```

Lab output, in order:

```
1  api/main.py:8:from common.money import fmt
   api/main.py:9:from common.settings import currency
   api/quotes.py:3:from common.money import to_cents
   worker/batch.py:4:from common.settings import currency
2  api/main.py:4:sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
   api/tests/conftest.py:4:sys.path.append(str(Path(__file__).resolve().parents[1]))
3  .env:1:PYTHONPATH=.
   .gitlab-ci.yml:2:  PYTHONPATH: "$CI_PROJECT_DIR"
   README.md:5:    PYTHONPATH=. python -m worker 1.10 2.20
   worker/Dockerfile:6:ENV PYTHONPATH=/app
4  .env:1: PYTHONPATH=.      (with .env in .gitignore, search 3 no longer found it)
7  .gitlab-ci.yml:7:    - pip install -r requirements.txt
   api/Dockerfile:3:COPY requirements.txt .
   api/Dockerfile:4:RUN pip install -r requirements.txt
   worker/Dockerfile:2:COPY requirements.txt /app/requirements.txt
   worker/Dockerfile:3:RUN pip install -r /app/requirements.txt
8  common/settings.py:5:    return os.environ.get("ACME_CURRENCY", "EUR")
```

Searches 5 and 6 found nothing (exit 1) before the walk. In
`recipes/independent-projects/`, search 5 printed
`billing/pyproject.toml:21:acme-core = { path = "../core", editable =
true }`.

A path hack or `PYTHONPATH` is a tie to whatever it makes importable:
read the line and name the folder it adds. `Path(__file__).resolve().
parent.parent` from `api/main.py` is the repository root, so it serves
`import common`; the conftest line adds `api/`, so it serves `from
quotes import Quote` in the tests.

## Copies

Git stores identical content under one hash, and normalises line endings
when it stores a file, so the index finds copies on every system:

```
git ls-files -s -- "*.py" | ForEach-Object { $f = $_ -split "\s+", 4; [pscustomobject]@{ Hash = $f[1]; Path = $f[3] } } | Where-Object Hash -ne "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391" | Group-Object Hash | Where-Object Count -gt 1 | ForEach-Object { $_.Group.Path -join " = " }
```

Lab: `common/money.py = worker/money.py`. The hash left out is the empty
file's: without it every pair of empty `__init__.py` files shows as a
copy. Files not yet committed are not in the index; `Get-ChildItem
-Recurse -File -Filter *.py | Where-Object Length -gt 0 | Get-FileHash |
Group-Object Hash` finds those too, but it also reads `.venv` and sees
line endings.

A copy that has since been edited has another hash. Find it by name,
then compare:

```
git ls-files -- "*.py" | Group-Object { Split-Path $_ -Leaf } | Where-Object Count -gt 1 | ForEach-Object { $_.Group -join ", " }
git diff --no-index common/money.py worker/money.py
```

`git diff --no-index` prints nothing and exits 0 when the two are the
same. In the lab one changed word (`ROUND_HALF_UP` to `ROUND_HALF_EVEN`)
gave exit 1 and the line, and `map_units.py` listed the pair under
`same file name in two units, different content`. Two copies that
differ are a question for the person (`core/monorepo.md`), never a
merge.

## Where each unit sits

| Sits | Signs |
| --- | --- |
| unpackaged | no `pyproject.toml`; run as `python <file>` or `python -m <folder>` with the repository root on the path |
| in one project with others | the root `pyproject.toml` has `[project]` and several packages or scripts; `map_units.py` prints `root project package ...` lines |
| its own project, its own lock | a `pyproject.toml` and a `uv.lock` in its folder, no workspace table above it |
| a workspace member | named by `members` in the root `[tool.uv.workspace]` and not by `exclude`; `uv workspace list` prints its name |
| another tool | `pants.toml`, `BUILD` or `BUILD.bazel` files, `MODULE.bazel`, `[tool.poetry]`, `[tool.pdm]` or Hatch workspace settings: recognised, never migrated unasked |

## What each unit installs

For a unit that is a project or a member:

```
uv tree --package acme-worker --no-dev --depth 1
uv export --package acme-api --no-dev --no-hashes
```

Lab, after the walk: `uv tree` printed `acme-common`, `click` and
`httpx` under `acme-worker v1.0.0`; `uv export` listed `-e ./api`, `-e
./common`, click, pydantic and their dependencies, and no httpx.

For an image, run its install line in a scratch copy of the build
context and read the `+` lines. In a lab project that builds two
services from one `pyproject.toml`, `uv sync --locked --no-dev
--no-editable` for the api image installed httpx, anyio, certifi, h11,
httpcore and idna, which only the worker imports: everything is
installed everywhere.
