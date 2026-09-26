# Debug: an install, import, build or resolution fails

**Verdict you produce:** the failing step, its message, the cause, the
fix, and the check.

```
step:    <resolve | fetch | build | install | import | run>
message: <the first error line and its "cause:" lines, copied>
cause:   <one sentence, with the file and line or the listing that shows it>
fix:     <the one change>
check:   <the command that now passes, and its line>
```

The hypothesis loop and reading the first error are seniority's habits;
this file is the packaging ladder. Import errors that happen only under
pytest (rootdir, import mode) are the pytest skill's.

## Find the step

Run the smallest command that reproduces it, with `-v` if the message is
thin, and read the first `error:` line and every `cause:` under it.

| Step | Typical message (uv 0.12.19, lab) | Go to |
| --- | --- | --- |
| resolve | `No solution found when resolving dependencies`, `Because ... we can conclude` | `core/dependencies.md` |
| resolve | `` `acme-core` is included as a workspace member, but is missing an entry in `tool.uv.sources` `` | `core/workspaces.md` |
| resolve | `was not found in the package registry`, `hint: An index URL (...) could not be queried due to a lack of valid authentication credentials (401 Unauthorized)` | `uv/config.md` (credentials) |
| resolve | `has no wheels with a matching platform tag` | `core/across-the-gap.md` |
| fetch | `invalid peer certificate: UnknownIssuer` | `uv/config.md` (the CA) |
| fetch | `dns error`, `failed to lookup address information`, a `pypi.org` or `files.pythonhosted.org` URL | the lock or config points outside: `uv/lockfile.md` |
| fetch | `Network connectivity is disabled, but the requested data wasn't found in the cache` | `--offline` with an empty cache for that URL |
| lock check | ``The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.`` | `pyproject.toml` or the index changed: `uv lock`, then read the diff |
| build | `Failed to resolve requirements from build-system.requires` | the backend is not on the mirror |
| build | `Unable to determine which files to ship inside the wheel`, `Expected a Python module at`, `Multiple top-level packages discovered` | `core/layout.md` |
| build | `Error getting the version from source` | `core/versioning.md` |
| install | `The wheel is invalid: invalid console script` | `core/entry-points.md` |
| install | `A virtual environment already exists at` | `uv venv --clear` |
| install | `The interpreter at /usr is externally managed` | `uv pip` found no venv and aimed at the system Python: pass `--python <venv>` |
| import | `ModuleNotFoundError` after install, tests pass in the repository | the wheel lacks the package: `core/layout.md` |
| run | `FileNotFoundError` for a file inside the package | package data missing: `core/layout.md` |
| run | the command prints an object (`<Group cli>`) and exits 1 | `core/entry-points.md` |

## Checks that separate the causes

- **Which interpreter and environment?** `uv run --no-sync python -c
  "import sys; print(sys.executable)"`. A bare `pip` inside `uv run` is
  whatever `pip` is on `PATH` (lab: `uv run pip --version` printed a pip
  from another venv, because the project's `.venv` has no pip).
- **Is it the wheel or the checkout?** Build and list the wheel
  (`core/build-and-inspect.md`); install it by path in a fresh venv and
  import from outside the checkout (`core/verify.md`).
- **Is it a stale install?** `uv pip install --find-links dist <name>`
  reused an older build of the same name and version from uv's cache
  (lab: the rebuilt wheel had the file, the install did not). Install
  the wheel by its path, or add `--refresh-package <name>`.
- **Is it the index?** Read `source = { registry = ... }` for the package
  in `uv.lock`.

## Never

- Never fix an import error by adding the source folder to `sys.path`,
  `PYTHONPATH` or pytest's `pythonpath`.
- Never clear uv's cache (`uv cache clean`) as a first move: it hides
  which install was stale and, air gapped, deletes what cannot be fetched
  again.
