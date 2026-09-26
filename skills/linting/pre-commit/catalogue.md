# Hooks worth having, and who owns each check

**What it decides:** which hooks a project's config should have, and
which skill owns the rule each hook enforces. pre-commit runs the check;
the owner decides what it checks. Every hook in the table ran, offline,
as a local hook on pre-commit 4.6.2, with the tools in the dev group.

| Hook (id) | Entry | Stage | Owner of the rule |
| --- | --- | --- | --- |
| `ruff-check` | `uv run --frozen ruff check --force-exclude` | pre-commit | linting |
| `ruff-format` | `uv run --frozen ruff format --force-exclude` | pre-commit | linting |
| `mypy` | `uv run --frozen mypy src`, `pass_filenames: false` | pre-commit | linting |
| `pyright` | `uv run --frozen pyright`, `pass_filenames: false` (from `pyright[nodejs]` in the dev group) | pre-commit | linting |
| `trailing-whitespace` | `uv run --frozen trailing-whitespace-fixer`, `types: [text]` | pre-commit | linting (file hygiene) |
| `end-of-file-fixer` | `uv run --frozen end-of-file-fixer`, `types: [text]` | pre-commit | linting (file hygiene) |
| `check-added-large-files` | `uv run --frozen check-added-large-files` | pre-commit | git (what may be committed) |
| `detect-private-key` | `uv run --frozen detect-private-key`, `types: [text]` | pre-commit | git (what may be committed) |
| `check-merge-conflict` | `uv run --frozen check-merge-conflict`, `types: [text]` | pre-commit | git |
| `check-yaml`, `check-toml` | `uv run --frozen check-yaml`, `types: [yaml]`; `check-toml`, `types: [toml]` | pre-commit | linting |
| `lint-imports` | `uv run --frozen lint-imports --no-logo`, `pass_filenames: false`, `types: [python]`; only where the project has contracts (`core/import-linter.md`) | pre-commit | architecture (the layer rules) |
| `uv-lock` | `uv lock --locked --offline`, `pass_filenames: false`, `files: ^(pyproject\.toml\|uv\.lock)$` | pre-commit | packaging (the lock matches `pyproject.toml`) |
| `issue-key` | `uv run --frozen python scripts/check_issue_key.py`, reading the file in its first argument | commit-msg | git (the message convention) |
| a fast test subset | `uv run --frozen pytest -m "not slow" -x -q`, `pass_filenames: false`, `always_run: true` | pre-push, only when the person asks for it | pytest (which subset, the marker) |

The `check-*` and fixer entries are console scripts of
`pre-commit-hooks` 6.0.0, installed from the dev group; their names and
`types` come from that package's `.pre-commit-hooks.yaml`.

`uv lock --locked --offline` printed `Resolved 18 packages` (exit 0)
when the lock matched, and `error: The lockfile at uv.lock needs to be
updated, but --locked was provided.` (exit 1) after a change to
`pyproject.toml`.

## What does not belong

- **Tests at the pre-commit stage.** They make every commit slow, and a
  commit is not where tests are judged. At most a fast subset at
  `pre-push`, when the person asks for it; the pytest skill owns which
  subset.
- **Two tools for one job**, such as black and `ruff format`, or isort
  and ruff's `I` rules: they rewrite each other's output and every
  commit loops (`ruff/format.md`).
- **A hook that needs the network**, such as a remote hook repository
  air gapped (`pre-commit/offline.md`).

## Adding a hook

1. Read the owner's rule (git's message convention, packaging's lock
   policy) before writing the check.
2. Add it as a local hook with the stage it needs; add the hook type
   to `default_install_hook_types` and set `default_stages:
   [pre-commit]` if it is not the pre-commit stage.
3. `validate-config`, `run --all-files` (or `--hook-stage <stage>`),
   then `install` again for a new hook type.
