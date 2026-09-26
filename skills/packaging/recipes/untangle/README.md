# Untangle: unpackaged units to one uv workspace

`before/` is the worst realistic state: two services (`api/`, `worker/`)
and a shared folder (`common/`), none of them a project. api reaches
common with `sys.path.insert` (`api/main.py`) and its tests with
`sys.path.append` (`api/tests/conftest.py`); worker needs `PYTHONPATH`
(CI, `worker/Dockerfile`, `.env`, the README); `worker/money.py` is a
copy of `common/money.py`; one unpinned `requirements.txt` goes into both
images and CI.

`after/` is the same repository after the five steps of
`core/monorepo-better.md`: a virtual root, members `common` (acme-common),
`api` (acme-api) and `worker` (acme-worker) in the folders they always
had, one `uv.lock`, bounded siblings with workspace sources, a console
script per service, Dockerfiles that sync `--package <member>`, and no
path hack, `PYTHONPATH` or copy left.

Every step, its commands and their output are in
`examples/untangle-monorepo.md`. Checked on uv 0.12.19, hatchling
1.32.4, Python 3.12, a local index standing in for the mirror, the
network cut: the baseline in `before/`, each step's tests, entry points,
wheels in clean venvs and image install lines, and `after/` replayed
from a fresh copy (`uv lock --check`, `2 passed`, six distributions
built, `quote 37.50 EUR` and `batch total 3.30 EUR` from the wheels
outside the checkout, `map_units.py` showing no sys.path lines, no
`PYTHONPATH` and no copies).

Change in `after/`: names, members, the mirror URL (`pyproject.toml` and
`uv.lock` name `https://pypi-mirror.example.com/simple`). The Dockerfiles
and `.gitlab-ci.yml` show what had to change; the deployment skill's
`recipes/monorepo/` has the Dockerfile to copy.
