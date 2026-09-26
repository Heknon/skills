# Worked example: a tangled repository walked to one workspace

Kinds: Monorepo, Workspace. Copy the order of the steps and the answer's
shape. Every output below is from the lab walk on uv 0.12.19, hatchling
1.32.4, Python 3.12, with a local index standing in for the mirror and
the network cut. The start is `recipes/untangle/before/`, the end
`recipes/untangle/after/`. No container engine was available: each image
was checked by extracting the committed tree as the build context,
running the Dockerfile's install line in it, and running its command
from another folder.

## The ask

> This is our monorepo and it is a mess. Let's make it better.

## Map (core/monorepo.md)

`uv run --no-project python <skill>\recipes\tools\map_units.py .`
(the lines that say `none` left out):

```
repository level: requirements.txt
units:
  api                      signs: Dockerfile, main guard in main.py
                           CI: .gitlab-ci.yml:11 job test-api: - pytest api/tests
                           CI: .gitlab-ci.yml:19 job build-api: - buildah bud -f api/Dockerfile -t acme-api .
  common                   signs: none; imported by api, worker
  worker                   signs: Dockerfile, __main__.py
                           CI: .gitlab-ci.yml:15 job test-worker: - pytest worker/tests
                           CI: .gitlab-ci.yml:23 job build-worker: - buildah bud -f worker/Dockerfile -t acme-worker .
imports across units:
  api/main.py:8: from common.money import fmt  -> common
  api/main.py:9: from common.settings import currency  -> common
  api/quotes.py:3: from common.money import to_cents  -> common
  worker/batch.py:4: from common.settings import currency  -> common
sys.path lines:
  api/main.py:4: sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
  api/tests/conftest.py:4: sys.path.append(str(Path(__file__).resolve().parents[1]))
PYTHONPATH settings:
  .env:1: PYTHONPATH=.
  .gitlab-ci.yml:2: PYTHONPATH: "$CI_PROJECT_DIR"
  README.md:5: PYTHONPATH=. python -m worker 1.10 2.20
  worker/Dockerfile:6: ENV PYTHONPATH=/app
requirement files read by builds and CI:
  requirements.txt <- .gitlab-ci.yml:7: - pip install -r requirements.txt
  requirements.txt <- api/Dockerfile:4: RUN pip install -r requirements.txt
  requirements.txt <- worker/Dockerfile:3: RUN pip install -r /app/requirements.txt
copies (same bytes in two units):
  common/money.py = worker/money.py  (sha256 25e11f302ed4)
```

Each line was confirmed with its search from `core/units-and-ties.md`.
`requirements.txt` holds `click`, `httpx`, `pydantic>=2` and `pytest`,
with no pins. The verdict:

```
units:
  api     service  signs: Dockerfile, main guard, CI test-api and build-api   sits: unpackaged
          ties: imports common (api/main.py:8, api/quotes.py:3); sys.path (api/main.py:4,
                api/tests/conftest.py:4); PYTHONPATH (.gitlab-ci.yml:2); reads requirements.txt
  worker  service  signs: Dockerfile, __main__.py, CI test-worker and build-worker   sits: unpackaged
          ties: imports common (worker/batch.py:4); copy of common/money.py (worker/money.py);
                PYTHONPATH (.gitlab-ci.yml:2, worker/Dockerfile:6, .env:1); reads requirements.txt
  common  library  signs: none; imported by api and worker   sits: unpackaged
spectrum: unpackaged units tied by paths
lock: none; requirements.txt shared by both images and CI
one lock fits: yes, because api and worker share common
problems: path hack (2), PYTHONPATH (4 places), copy (worker/money.py), no lock,
          everything installed everywhere (pytest and every dependency in both images)
questions: none
```

No question: the shared library decides one workspace, the copy is
identical, every unit has a Dockerfile and CI job.

## Baseline, the way CI and the images run today

```
PYTHONPATH=<root> pytest -q api/tests          1 passed in 0.07s
PYTHONPATH=<root> pytest -q worker/tests       1 passed in 0.04s
python api/main.py quote 12.50 3               quote 37.50 EUR
PYTHONPATH=. python -m worker 1.10 2.20        batch total 3.30 EUR
pytest -q api/tests   (no PYTHONPATH)          E   ModuleNotFoundError: No module named 'common'
python -m worker 1.10 2.20   (from /tmp)       No module named worker
```

## Step 1: the copy

```
$ git diff --no-index --stat common/money.py worker/money.py      (nothing; exit 0)
```

`worker/batch.py:5` changed from `from worker.money import fmt, to_cents`
to `from common.money import fmt, to_cents`; `worker/money.py` deleted.
Check: `git grep -n -E "worker\.money|^\s*from money|^\s*import money"`
exit 1; worker tests `1 passed`; `batch total 3.30 EUR` the README way
and the image way. Docker and CI: nothing.

## Step 2: a lock for what is there

Root `pyproject.toml` with `[tool.uv.workspace] members = []` and the
mirror, then:

```
$ uv add --group legacy -r requirements.txt
warning: No `requires-python` value found in the workspace. Defaulting to `>=3.12`.
Resolved 18 packages in 3ms
$ uv remove --group legacy pytest
$ uv add --dev "pytest>=9.1.1"
```

The groups read `dev = ["pytest>=9.1.1"]` and `legacy = ["click>=8.5.0",
"httpx>=0.28.1", "pydantic>=2"]`. Before `default-groups` was set:

```
$ uv run python -c "import click"
ModuleNotFoundError: No module named 'click'
```

With `[tool.uv] default-groups = ["dev", "legacy"]`: `uv lock` printed
`Resolved 18 packages`, `uv run` had all four, and `uv sync --no-dev`
removed only pytest and its dependencies. `requirements.txt` deleted.

Docker and CI (for the deployment skill): CI's `pip install -r
requirements.txt` became `uv sync --locked` and `pytest` became `uv run
pytest`; both Dockerfiles `COPY . .` and `RUN uv sync --locked --no-dev
--no-editable`, a `.dockerignore` with `.venv`; the worker image keeps
`ENV PYTHONPATH=/app`. Check, through `uv run` and in each image:
`1 passed` twice, `quote 37.50 EUR`, `batch total 3.30 EUR`; the images
installed 12 packages, pytest not among them.

## Step 3: common becomes acme-common

```
$ git mv common/__init__.py common/money.py common/settings.py common/src/acme_common/
$ uv init --lib --name acme-common --build-backend hatchling --vcs none --no-readme --no-pin-python common
Adding `acme-common` as member of workspace `<root>`
Initialized project `acme-common` at `<root>/common`
```

`common/pyproject.toml`: version `1.0.0`, a description, no `authors`,
`requires = ["hatchling>=1.27"]`. Five imports renamed to
`acme_common`; `git grep -n -E "^\s*(from|import)\s+common\b"` exit 1.
`api/main.py:4`'s `sys.path.insert` deleted: it only served `common`.

```
$ uv lock
Resolved 19 packages in 5ms
Added acme-common v1.0.0
$ uv run pytest api/tests                            1 passed    (no PYTHONPATH)
$ PYTHONPATH=. uv run pytest worker/tests            1 passed
$ uv run python api/main.py quote 12.50 3            quote 37.50 EUR
$ PYTHONPATH=. uv run python -m worker 1.10 2.20     batch total 3.30 EUR
$ uv build --package acme-common
Successfully built dist/acme_common-1.0.0-py3-none-any.whl
```

`inspect_dist.py --against common/src/acme_common`: `built by: hatchling
1.32.4`, `every source file is in the distribution`; in a clean venv,
from `/tmp`, `fmt(to_cents('1.10'), 'EUR')` printed `1.10 EUR`. Docker
and CI: nothing; both images installed `acme-common==1.0.0` and ran.

## Step 4: api becomes acme-api

`api/main.py` and `api/quotes.py` moved to `api/src/acme_api/`;
`api/tests/conftest.py` deleted.

```
$ uv init --package --name acme-api --build-backend hatchling --vcs none --no-readme --no-pin-python api
[project.scripts]
acme-api = "acme_api:main"
```

It also wrote `api/src/acme_api/__init__.py` with `print("Hello from
acme-api!")`. Fixed: the script to `acme_api.main:cli`, the
`__init__.py` emptied, `from quotes import Quote` to `from
acme_api.quotes import Quote` in `main.py` and the test.

```
$ uv add --package acme-api "acme-common>=1.0,<2" "click>=8.5.0" "pydantic>=2"
Resolved 20 packages in 7ms
$ uv remove --group legacy pydantic
$ uv run pytest api/tests                   1 passed
$ uv run acme-api quote 12.50 3             quote 37.50 EUR
$ uv build --package acme-api
Successfully built dist/acme_api-1.0.0-py3-none-any.whl
$ uv run --no-project python <skill>\recipes\tools\inspect_dist.py dist\acme_api-1.0.0-py3-none-any.whl --against api\src\acme_api
  Requires-Dist: acme-common<2,>=1.0
  Requires-Dist: click>=8.5.0
  Requires-Dist: pydantic>=2
  acme-api = acme_api.main:cli
  every source file is in the distribution
```

Both wheels by path in a clean venv, from `/tmp`: `acme-api quote 12.50
3` printed `quote 37.50 EUR`; the tests against the wheels (`uv run
--isolated --no-project --with <both wheels> --with pytest pytest
api/tests`) `1 passed`. The worker, still outside, passed as before.

Docker (for the deployment skill): `RUN uv sync --locked --no-dev
--no-editable --package acme-api`, `CMD ["/app/.venv/bin/acme-api", ...]`.
Its sync installed 8 packages: acme-api, acme-common, annotated-types,
click, pydantic, pydantic-core, typing-extensions, typing-inspection; no
httpx, although `legacy` still named it.

## Step 5: worker becomes acme-worker, and the transition goes

Moved to `worker/src/acme_worker/`. `uv init --package` kept the empty
`__init__.py` and wrote `acme-worker = "acme_worker:main"`; run as it
was, the script failed with `ImportError: cannot import name 'main' from
'acme_worker'`. Fixed to `acme_worker.batch:main`; two imports of
`worker.batch` renamed.

```
$ uv add --package acme-worker "acme-common>=1.0,<2" "click>=8.5.0" "httpx>=0.28.1"
$ uv remove --group legacy click httpx
```

Then the empty `legacy` group and `default-groups` deleted, and
`PYTHONPATH` removed from `.gitlab-ci.yml`, `.env` and the README; the
worker Dockerfile syncs `--package acme-worker` and runs `acme-worker`.

```
$ git grep -n PYTHONPATH                          (nothing; exit 1)
$ git grep -n -E "sys\.path\.(insert|append)"     (nothing; exit 1)
$ uv lock --check
Resolved 21 packages in 1ms
$ uv workspace list
acme-api
acme-common
acme-worker
$ uv run pytest api/tests worker/tests            2 passed
$ uv run acme-worker 1.10 2.20                    batch total 3.30 EUR
$ uv build --all-packages                         six "Successfully built" lines
$ uv pip list, in a clean venv per service with its wheels installed by path:
acme-api venv: acme-api acme-common annotated-types click pydantic pydantic-core typing-extensions typing-inspection
acme-worker venv: acme-common acme-worker anyio certifi click h11 httpcore httpx idna typing-extensions
```

From `/tmp`, in those venvs: `quote 37.50 EUR` and `batch total 3.30
EUR`; the tests against the wheels passed for both. The worker image's
sync installed 10 packages, none of pydantic. `map_units.py` now shows
three units with a `pyproject.toml` each, the imports of `acme_common`,
two workspace sources, one workspace, and no sys.path lines, no
`PYTHONPATH`, no copies.

## The answer

```
## Result
The repository held three units: two services (api, worker) and a
library they share (common), reached by two sys.path lines, PYTHONPATH
in four places and a copied module, with one unpinned requirements.txt
installed into both images. It is now one uv workspace in the same
folders: acme-common, acme-api and acme-worker, one uv.lock, the sibling
bounded (acme-common>=1.0,<2), a console script per service. Five
commits, one per step, each checked.

## Checked
- Baseline and after every step: each unit's tests (1 passed each) and
  entry points (quote 37.50 EUR, batch total 3.30 EUR).
- uv lock --check; uv workspace list: acme-api, acme-common, acme-worker.
- Every wheel built and inspected: every source file in the
  distribution, Requires-Dist acme-common<2,>=1.0.
- Each service's wheels in a clean venv, run from outside the checkout;
  the api venv has no httpx, the worker venv no pydantic, neither pytest.
- Each image's install line in a copy of the build context: only its
  unit's packages.

## Not checked
- The images themselves (no container engine here) and the pipeline:
  run build-api and build-worker once.
- Windows.

## Needs a person
- The deployment skill, or whoever owns them, to review the Dockerfile
  and .gitlab-ci.yml changes listed in steps 2, 4 and 5.
```
