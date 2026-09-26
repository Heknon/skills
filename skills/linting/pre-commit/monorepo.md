# pre-commit in a monorepo or uv workspace

**What it decides:** where hooks for each member live, which files each
hook sees, and how each tool finds the member's settings and packages.
Verified on pre-commit 4.6.2, uv 0.12.19, mypy 2.3.1 and ruff 0.16.9,
in a uv workspace with `services/api`, `services/worker` and
`packages/common`. The workspace itself (members, one lock) is the
packaging skill's.

## One config, at the repository root

The installed hook names `--config=.pre-commit-config.yaml` and runs
from the repository root, so **a `.pre-commit-config.yaml` in a member
folder is never used by a commit.** Run by hand from that folder,
pre-commit does use it, which gives a false answer:

*Lab:* a stale `services/api/.pre-commit-config.yaml` ran `mypy
--ignore-missing-imports` over every file of the repository and said
`Passed`, while the member's strict mypy found an error. Move what is
worth keeping into the root config, delete the nested file (or name it
as unused for the person), and always run from the root.

## A hook per member, scoped with `files`

```yaml
      - id: mypy-api
        name: mypy (services/api, strict)
        entry: uv run --frozen --all-packages mypy --config-file services/api/pyproject.toml services/api/src
        language: system
        files: ^services/api/
        types_or: [python, pyi]
        pass_filenames: false
```

- `files` is a regex from the root. *Lab:* with only a worker file
  staged, this hook printed `(no files to check)Skipped`.
- `pass_filenames: false` and an explicit path: mypy checks the member
  as a whole, the same way on every run.
- `--config-file`: mypy picks its config by the folder it starts in, and
  hooks start at the root, where it printed `Config File: Default`.
  `uv run --frozen --directory services/api mypy src` also worked.
- `--all-packages`: `uv run` installs the root project's dependencies
  and dev group by default, not the members. *Lab, fresh `.venv`:*
  plain `--frozen` left `common` uninstalled; `--package api` installed
  only `api` and `common` and no mypy, so the `mypy` from `PATH` ran and
  reported `import-not-found`; `--frozen --all-packages` gave the right
  result.
- ruff needs one hook: each file uses the closest config with a
  `[tool.ruff]` table, so members with their own settings get them
  (`ruff/config.md`). A member's table replaces the root's unless it
  uses `extend`.
- A workspace has one lock, so one version of each tool. Members that
  need different versions are separate projects with their own locks,
  a packaging decision; give each its own hook, scoped with `files`.

Full config: `recipes/pre-commit-workspace/`.

## Checking it

```
uv run --frozen pre-commit validate-config
uv run --frozen pre-commit run --all-files          # from the root
uv run --frozen pre-commit run mypy-api --all-files
```

## prek is different here

prek (`pre-commit/alternatives.md`) treats nested configs as projects:
in the lab it ran `services/api/.pre-commit-config.yaml` from inside
`services/api`, as well as the root one. If the repository uses prek,
nested configs are live.
