# Hooks with no network

**What it decides:** how each hook gets its tool when only the package
mirror is reachable. Verified on pre-commit 4.6.2 with the network cut
off (a network namespace with a local package index as the "mirror").

## What fails, and how

Every `repo: https://...` entry is a git repository pre-commit clones on
first use. Air gapped:

```
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
An unexpected error has occurred: CalledProcessError: command: ('git', 'fetch', 'origin', '--tags')
return code: 128
...
    fatal: unable to access 'https://github.com/pre-commit/pre-commit-hooks/': Could not resolve host: github.com
```

exit 3. `pre-commit autoupdate` fails the same way. Nothing in the
config can fix a URL the machine cannot reach; change where the hooks
come from.

## 1. Local hooks that run the project's tools (preferred)

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run --frozen ruff check --force-exclude
        language: system
        types_or: [python, pyi]
        require_serial: true
      - id: check-added-large-files
        name: check for added large files
        entry: uv run --frozen check-added-large-files
        language: system
```

- The versions are the lock's, the same as CI's; `pre-commit-hooks`
  (its `check-added-large-files`, `detect-private-key`,
  `end-of-file-fixer`, `trailing-whitespace-fixer`, and the rest) goes
  in the dev group like ruff. *Lab:* seven such hooks passed with no
  network at all.
- `uv run --frozen`, not `--no-sync`: in a checkout without a synced
  `.venv`, `--no-sync` ran a global ruff of another version
  (`core/run-like-ci.md`); `--frozen` installed the lock's from uv's
  cache, and fails loudly when it cannot.
- Take each hook's `entry` and `types` from the hook repository's
  `.pre-commit-hooks.yaml` if you have it; for pre-commit-hooks 6.0.0,
  `trailing-whitespace` runs `trailing-whitespace-fixer` and uses
  `types: [text]`. Full config: `recipes/pre-commit-project/`.

## 2. `language: python` hooks installed from the mirror

pre-commit builds a virtualenv per hook with `virtualenv`, then runs
`python -mpip install . <additional_dependencies>` in it (read in the
installed `pre_commit` package, `languages/python.py`). It is **pip,
not uv**:

| Setting | Offline result in the lab |
| --- | --- |
| none | `No matching distribution found for setuptools>=40.8.0`, after five retries to `pypi.org` |
| `UV_DEFAULT_INDEX`, `UV_INDEX_URL` | the same failure: uv's settings do not reach pip |
| `PIP_INDEX_URL=<mirror>/simple` | installed and ran |
| `PIP_CONFIG_FILE` naming a file with `[global]` `index-url = <mirror>/simple` | installed and ran |
| a mirror without `setuptools` | failed: the `.` being installed (pre-commit's placeholder package for `repo: local`, or the hook repository) is built with setuptools |

In PowerShell, for the session: `$env:PIP_INDEX_URL =
"https://<mirror>/simple"`. A mirror behind the company's certificate
also needs `PIP_CERT` or `cert =` in the pip config. The per-user pip
config on Windows is `%APPDATA%\pip\pip.ini` (not run on Windows).

Once built, the environments stay in `PRE_COMMIT_HOME` (default
`~/.cache/pre-commit`) and later runs needed no index at all. Build them
while the mirror is reachable with `pre-commit install-hooks` (or
`install --install-hooks`).

## 3. Hook repositories mirrored into GitLab

```yaml
  - repo: https://gitlab.example.internal/mirrors/ruff-pre-commit
    rev: v0.16.9
    hooks:
      - id: ruff-check
```

*Lab (a bare git mirror standing in for GitLab):* worked offline with
`PIP_INDEX_URL` set, because the repository is itself a `language:
python` hook that installs `ruff==0.16.9` and needs setuptools. Pin
`rev` to a tag or commit: a branch name gets `appears to be a mutable
reference ... Mutable references are never updated after first install`.
Someone must keep the mirror updated; ask who does.

## Housekeeping

| Command | Does |
| --- | --- |
| `pre-commit gc` | removes cached repositories no config uses (`0 repo(s) removed.`) |
| `pre-commit clean` | deletes `PRE_COMMIT_HOME`; offline, everything must then be rebuilt from the mirror |
| `$env:PRE_COMMIT_HOME = "<folder>"` | moves the cache, for example to a CI cache folder |
