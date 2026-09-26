# Installing the git hooks

**What it decides:** which hook scripts exist in `.git/hooks`, what each
runs, and how to install without breaking another tool's hooks. Verified
on pre-commit 4.6.2 and git 2.43.

## Install from the project's environment

```
uv run --frozen pre-commit install
```

It installs one script per hook type in `default_install_hook_types`
(default `[pre-commit]`), or the types given with `-t`:

```
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/commit-msg
```

A hook type that is not installed never runs, whatever `stages` says.
After adding a `commit-msg` or `pre-push` hook to the config, add the
type to `default_install_hook_types` and run `install` again.

## The interpreter it records

The script starts with the absolute path of the Python that ran
`install`, then falls back:

```
INSTALL_PYTHON=/path/to/project/.venv/bin/python
ARGS=(hook-impl --config=.pre-commit-config.yaml --hook-type=pre-commit)
```

1. `INSTALL_PYTHON` if that file exists;
2. otherwise `pre-commit` on `PATH`, which may be another version;
3. otherwise the commit fails: `` `pre-commit` not found.  Did you
   forget to activate your virtualenv? ``

*Lab:* installed with `uvx pre-commit@4.6.2 install`, the path was in
uv's cache (`.../archive-v0/<hash>/bin/python`); after `uv cache clean`
the commit used a `pre-commit` from `PATH`, and without one it failed as
in 3. Installed with `uv run`, the path is the project's `.venv`
(on Windows `.venv\Scripts\python.exe`; not run on Windows), which
survives `uv sync`. Install with `uv run`, never with `uvx`, and run
`install` again after moving or recreating the project folder.

The config path is relative (`--config=.pre-commit-config.yaml`), from
the repository root: a `.pre-commit-config.yaml` in a subfolder is never
used by commits (`pre-commit/monorepo.md`).

## `core.hooksPath` is set

```
[ERROR] Cowardly refusing to install hooks with `core.hooksPath` set.
hint: `git config --unset-all core.hooksPath`
```

The hint switches off whatever the hooks path runs, such as a company
secret scan. Git's settings are the git skill's; the person decides.
Stop, read what is in the hooks path, and offer:

- **Call pre-commit from the existing hook.** At the end of the script
  in the hooks path (for example `.githooks/pre-commit`):

  ```sh
  # Also run the project's pre-commit hooks (see .pre-commit-config.yaml).
  exec uv run --frozen pre-commit run
  ```

  *Lab:* the existing check ran first, then the ruff hook failed the
  commit on an unused import. `pre-commit run` with no arguments checks
  the staged files, which is what the pre-commit stage does.
- **Unset the hooks path**, only if the person decides the other hooks
  are no longer needed.

## An existing hook script

If `.git/hooks/pre-commit` exists and is not pre-commit's, `install`
moves it to `pre-commit.legacy` and runs both:

```
Running in migration mode with existing hooks at .git/hooks/pre-commit.legacy
Use -f to use only pre-commit.
```

*Lab:* the commit printed the old hook's output, then pre-commit's.
`install -f` deletes the old one; ask before using it.

## Worktrees, clones and a missing config

- Hooks live in the shared `.git/hooks` (`git rev-parse --git-path
  hooks`); a `git worktree` uses them without a new install. *Lab:* the
  worktree's commit ran the hooks, with the main checkout's
  `INSTALL_PYTHON`, and `uv run --no-sync` inside the hooks then ran a
  global tool, because the worktree had no `.venv` of its own. Hence
  `uv run --frozen` in hook entries.
- A fresh clone has no hooks until someone runs `install`.
- A commit in a repository with the hook but no config failed with `No
  .pre-commit-config.yaml file was found`; `PRE_COMMIT_ALLOW_NO_CONFIG=1`
  gets past it once, `install --allow-missing-config` for good.
- `pre-commit uninstall` removes its scripts and puts a `.legacy` hook
  back (`Restored previous hooks to .git/hooks/pre-commit`).
