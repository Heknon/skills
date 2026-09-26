# Offline pre-commit hooks for one uv project

`.pre-commit-config.yaml` here runs every check from the project's own
environment, so nothing is fetched and every version is the lock's.

## Needs

In `pyproject.toml`, the dev group (the packaging skill adds it):

```toml
[dependency-groups]
dev = ["ruff==0.16.9", "mypy==2.3.1", "pre-commit==4.6.2", "pre-commit-hooks==6.0.0"]
```

Then, once per clone: `uv sync`, `uv run --frozen pre-commit install`.

## Change

Only the mypy path (`src`) and the hooks the project does not want.
Add a `commit-msg` or `pre-push` hook as `pre-commit/catalogue.md`
shows, with its type in `default_install_hook_types`.

## Checked (*lab*, pre-commit 4.6.2, network cut off after `uv sync`)

```
$ uv run --frozen pre-commit validate-config        # no output, exit 0
$ uv run --frozen pre-commit install
pre-commit installed at .git/hooks/pre-commit
$ uv run --frozen pre-commit run --all-files
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check for added large files..............................................Passed
detect private key.......................................................Passed
check for merge conflicts................................................Passed
check toml...............................................................Passed
uv.lock matches pyproject.toml...........................................Passed
ruff check...............................................................Passed
ruff format..............................................................Passed
mypy.....................................................................Passed
```

A commit adding `import os` to a new module was refused offline with
`ruff check....Failed`, `- exit code: 1`, ``F401 [*] `os` imported but
unused``, and `mypy....(no files to check)Skipped` for the commit that
changed only the config.
