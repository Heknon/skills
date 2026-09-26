# uv commands used by this skill

uv 0.12.19; every flag here is in `uv help <command>` on that version and
was run in the lab. For a flag not listed, read `uv help <command>`
rather than recalling one.

## Project

| Command | Does | Notes (lab) |
| --- | --- | --- |
| `uv lock` | resolves and writes `uv.lock` | keeps locked versions that still fit |
| `uv lock --check` / `--locked` | fails if the lock would change | exit 1, ``needs to be updated, but `--check` was provided`` |
| `uv lock --upgrade-package <name>` | re-resolves one package | `Updated acme-utils v9.0.0 -> v1.4.0` |
| `uv lock --dry-run` | prints `Add ...`, `Update ...`; writes nothing | |
| `uv sync` | makes `.venv` match the lock exactly, project editable | removes packages the lock does not list (`- rich==15.0.0`) |
| `uv sync --locked` | the same, and fails on a stale lock | CI's form (deployment skill) |
| `uv sync --frozen` | installs from the lock without checking it | never to get past a stale lock |
| `uv sync --no-dev`, `--group <g>`, `--extra <e>`, `--all-extras` | choose groups and extras | `--no-dev` drops the `dev` group |
| `uv sync --no-editable` | installs the project as a built wheel | for images |
| `uv sync --package <member>` | one workspace member and what it needs | `core/workspaces.md` |
| `uv sync --all-packages` | every member | |
| `uv run <cmd>` | syncs (adding, not removing) then runs | rebuilt the project after `pyproject.toml` changed |
| `uv run --no-sync <cmd>` | runs without touching the environment | for looking |
| `uv run --package <member> <cmd>` | runs in the workspace env with that member synced | |
| `uv run --isolated --no-project --with <wheel> --with pytest pytest tests` | a throwaway env with only those | tests against a built wheel |
| `uv add <req>`, `uv remove <name>` | edit `pyproject.toml`, lock, sync | `core/metadata.md` |
| `uv tree`, `--depth 1`, `--invert --package <name>` | the resolved tree; who needs a package | |
| `uv version [--bump <part>] [--dry-run] [--short] [--package <m>]` | read or set a static version | `core/versioning.md` |
| `uv export --no-emit-project --no-dev -o requirements.txt` | the lock as pinned requirements with hashes | `--package`, `--no-emit-workspace` for one member |
| `uv init --package [--name <n>] <dir>` | a src-layout project on uv_build | `--build-backend hatch\|setuptools\|...` |
| `uv workspace list [--paths]`, `uv workspace dir --package <m>` | members and their folders | `uv workspace metadata` is experimental and warns |

## Build and publish

| Command | Does |
| --- | --- |
| `uv build` | sdist, then the wheel from it, into `dist\` |
| `uv build --sdist` / `--wheel` | one of them; `--wheel` builds from the tree |
| `uv build --package <m>` / `--all-packages` | workspace members; output in the root's `dist\` |
| `uv build --clear`, `--out-dir <d>`, `--no-create-gitignore` | output handling |
| `uv build --force-pep517` | always call the backend (uv_build from the index too) |
| `uv publish --index <name> --dry-run --trusted-publishing never <files>` | checks the files against the index's `url`; uploads nothing |
| `uv publish --publish-url <url> --check-url <index url> <files>` | uploads, skipping files the index already has |

`uv publish` with no URL targets `https://upload.pypi.org/legacy/`
(`core/publish.md`).

## pip interface (outside a project's lock)

| Command | Use here |
| --- | --- |
| `uv venv <dir> --python 3.12 [--clear]` | a scratch venv; an existing one needs `--clear` |
| `uv pip install --python <venv python> <wheel path>` | install a built wheel to verify it |
| `uv pip install ... --dry-run --find-links dist <name>` | would these wheels resolve together? |
| `uv pip install --offline --no-index --find-links wheelhouse -r requirements.txt` | a wheelhouse install |
| `uv pip compile <reqs> --python-platform <target> --python-version 3.12 --no-index --find-links <dir>` | does a wheelhouse fit another platform? |
| `uv pip list`, `uv pip show <name>` | what is installed |

`uv pip install` into a project's `.venv` is undone by the next `uv
sync`; use it only for scratch venvs. With no venv found and
`UV_PYTHON` naming a system Python, it aimed at that Python and stopped:
`The interpreter at /usr is externally managed`.

## Global flags

| Flag | Does |
| --- | --- |
| `--offline` | no network; only the cache (`UV_OFFLINE`) |
| `--no-cache`, `--refresh-package <name>` | ignore the cache for everything or for one package |
| `-v` | debug lines: which config file, which index, which version selected |
| `--directory <dir>`, `--project <dir>` | run as if in another folder |
| `--no-config` | ignore `pyproject.toml` and `uv.toml` settings |
