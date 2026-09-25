# Python in GitLab CI

Python runs through uv, as in the team's conventions. Every job below ran
on GitLab 19.4.1 with uv 0.12.19, in the recipes.

## The job image

An image with uv and Python from the mirror, such as the mirror of
`ghcr.io/astral-sh/uv:0.12-python3.12-trixie-slim`. Set
`UV_PYTHON_DOWNLOADS: never` so uv uses the image's Python and never tries
to download one (which fails air gapped).

## Install, lint, test

```yaml
.uv:
  image: $PYTHON_IMAGE
  variables:
    UV_CACHE_DIR: $CI_PROJECT_DIR/.uv-cache
    UV_LINK_MODE: copy
  cache:
    key:
      files: [uv.lock]
    paths: [.uv-cache]
  before_script:
    - uv sync --locked
  after_script:
    - uv cache prune --ci

test:
  extends: .uv
  script:
    - uv run pytest --junitxml=report.xml --cov --cov-report=term --cov-report=xml:coverage.xml
  coverage: '/^TOTAL.*\s(\d+(?:\.\d+)?)%$/'
  artifacts:
    when: always
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

- `uv sync --locked` fails if `uv.lock` does not match `pyproject.toml`:
  the pipeline tests exactly what was locked. `--frozen` skips the check;
  do not use it in CI.
- The cache must be inside the project folder to be cached;
  `uv cache prune --ci` keeps only what is worth caching. `UV_LINK_MODE:
  copy` avoids hard-link warnings across file systems.
- In a uv workspace: `uv sync --locked --package <member>` installs one
  member and its dependencies, including that member's own
  `dependency-groups`; a `dev` group at the workspace root is not
  installed by it, so each member declares its test tools (seen in the
  lab monorepo).
- After a sync, `uv run --no-sync <tool>` runs without checking the
  environment again.

## The package index, air gapped

The index belongs in `pyproject.toml`, so developers and CI resolve from
the same place and `uv.lock` records it:

```toml
[[tool.uv.index]]
name = "internal"
url = "https://pypi-mirror.example.com/simple"
default = true
```

Credentials never go in the file. uv reads, for an index named `internal`,
`UV_INDEX_INTERNAL_USERNAME` and `UV_INDEX_INTERNAL_PASSWORD`, or a
`.netrc` file. Do not point CI at another index with `UV_DEFAULT_INDEX`:
the lock records the index of each package, and in the lab `uv sync
--locked` with a different `UV_DEFAULT_INDEX` went to resolve against the
new index instead of installing the locked set.

An index behind the internal CA needs the CA: `SSL_CERT_FILE` pointing at
it (a File variable), or the CA installed in the job image. Without it:
`invalid peer certificate: UnknownIssuer` (lab).

## GitLab's PyPI registry

- Publish from a tag pipeline with the job token
  (`recipes/ci-components/templates/python-publish.yml`, ran in the lab):
  ```yaml
  variables:
    UV_PUBLISH_URL: $CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/pypi
    UV_PUBLISH_USERNAME: gitlab-ci-token
  script:
    - uv build --out-dir dist
    - UV_PUBLISH_PASSWORD="$CI_JOB_TOKEN" uv publish dist/*
  ```
  The same version cannot be uploaded twice; bump the version.
- Install from it: the project index is
  `$CI_API_V4_URL/projects/<id>/packages/pypi/simple`, the group index
  `$CI_API_V4_URL/groups/<id>/-/packages/pypi/simple`. In CI, user
  `gitlab-ci-token` and password `$CI_JOB_TOKEN`, with the package's
  project allowing this project's job token when it is private
  (`gitlab/job-token.md`). *lab:* `uv pip install --index-url
  "http://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.lab/api/v4/projects/4/packages/pypi/simple" sample-app`
  installed the package published by the components project. Outside CI,
  a personal or deploy token with `read_api` or `read_package_registry`.

## In the image build

The Dockerfile recipe runs `uv sync --locked --no-dev --no-editable` in a
build stage and copies `/app/.venv` into a runtime stage with the same
Python minor version. Index credentials reach the build as a `netrc`
build secret and the internal CA as a `ca` build secret
(`gitlab/images.md`).
