# Worked example: hooks that need GitHub, air gapped

Kinds: Pre-commit. Outputs from a lab run on pre-commit 4.6.2 with the
network cut off (a network namespace).

## The ask

> pre-commit fails with the error below. We're air gapped, there's only
> our package mirror. Make our hooks work.

```
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
An unexpected error has occurred: CalledProcessError: command: ('git', 'fetch', 'origin', '--tags')
...
    fatal: unable to access 'https://github.com/pre-commit/pre-commit-hooks/': Could not resolve host: github.com
```

The config listed three hook repositories: `pre-commit-hooks` v6.0.0
(four hooks), `ruff-pre-commit` v0.16.9 and `mirrors-mypy` v2.3.1.

## Steps

1. **Read the error** (`pre-commit/offline.md`): a git fetch of a GitHub
   URL. Each remote repository will fail the same way; `autoupdate`
   would too.
2. **Look at what the project already has.** The dev group pins
   `ruff==0.16.9`, `mypy==2.3.1`, `pre-commit==4.6.2` and
   `pre-commit-hooks==6.0.0`: every tool the hooks need, at the same
   versions, from the mirror.
3. **Rewrite as local hooks** that run those tools with
   `uv run --frozen`, taking each `entry` and `types` from
   pre-commit-hooks' own manifest (`trailing-whitespace` runs
   `trailing-whitespace-fixer`, `types: [text]`). The result is
   `recipes/pre-commit-project/` without its extra hooks.
4. **Validate and run**, still offline:
   ```
   > uv run --frozen pre-commit validate-config
   > uv run --frozen pre-commit run --all-files
   trim trailing whitespace.................................................Passed
   fix end of files.........................................................Passed
   check for added large files..............................................Passed
   detect private key.......................................................Passed
   ruff check...............................................................Passed
   ruff format..............................................................Passed
   mypy.....................................................................Passed
   ```
5. **Install from the project's environment**:
   `uv run --frozen pre-commit install`, so the hook records the
   project's `.venv` Python and not one in a cache.

## The answer

```
## Result
.pre-commit-config.yaml now uses only `repo: local` hooks that run the
project's own tools with `uv run --frozen`: the four pre-commit-hooks
checks (from the pre-commit-hooks package already in the dev group),
ruff check, ruff format and mypy. Nothing is fetched from GitHub, and
the versions are the ones in uv.lock, the same as CI. The hook is
installed from the project environment.

## Checked
- pre-commit validate-config: no errors.
- pre-commit run --all-files with no network: all 7 hooks Passed.

## Not checked
- Windows: the hooks were run on Linux; the entries use forward slashes
  and `uv`, which pre-commit finds through PATHEXT.
- An internal GitLab mirror of the hook repositories was not needed.
```
