# Worked example: releasing one workspace member

Kinds: Member release, Version, Publish. Copy the order of the steps and
the answer's shape. Outputs are from a lab run on uv 0.12.19 with
`recipes/workspace/`, and a local test index standing in for the internal
index (the person had asked for the upload; nothing went near a public
index).

## The ask

> Release acme-api 0.5.0 to the internal index. Upload it yourself; the
> credentials are in UV_INDEX_INTERNAL_USERNAME and _PASSWORD.

## Steps

1. **Where does it go?** The root `pyproject.toml` has
   `[[tool.uv.index]] name = "internal"` with a `publish-url` and
   `explicit = true`. The credentials are there: `[bool]$env:
   UV_INDEX_INTERNAL_PASSWORD` is `True`; the value is never printed.
2. **Version** (`core/versioning.md`):
   ```
   uv version --package acme-api --short            # 0.4.0
   uv version --package acme-api --bump minor       # acme-api 0.4.0 => 0.5.0
   ```
3. **Build that member only, clean:**
   `uv build --package acme-api --clear` gives
   `dist/acme_api-0.5.0.tar.gz` and `dist/acme_api-0.5.0-py3-none-any.whl`.
4. **Read what it will require** (`inspect_dist.py`):
   ```
   Version: 0.5.0
   Requires-Dist: acme-core<2,>=1.2
   Requires-Dist: click>=8.1
   built by: hatchling 1.32.4
   ```
   The sibling is bounded. Verify the wheel in a fresh venv
   (`core/verify.md`): `acme-api 1.10 2.20` printed `total 3.30`.
5. **Can a consumer install it?** Dry run from the wheel's path, with the
   internal index on the command line (`core/member-release.md`):
   ```
   error: No solution found when resolving dependencies
     cause: Because acme-core was not found in the package registry and all versions of acme-api depend on acme-core>=1.2,<2, we can conclude that all versions of acme-api cannot be used.
   ```
   acme-core has never been published. acme-api 0.5.0 would be
   uninstallable. Stop and ask: the person agreed to release acme-core
   1.2.0 first, unchanged.
6. **acme-core 1.2.0:** `uv build --package acme-core`, inspected, then
   ```
   uv publish --index internal --dry-run --trusted-publishing never dist\acme_core-1.2.0*
   uv publish --index internal --trusted-publishing never dist\acme_core-1.2.0*
   ```
   `Checking 2 files against http://127.0.0.1:8900/`, then `Uploading
   acme_core-1.2.0-py3-none-any.whl`, `Uploading acme_core-1.2.0.tar.gz`.
7. **Check again:** the same dry run now says `+ acme-core==1.2.0`,
   `+ click==8.5.0`.
8. **acme-api 0.5.0:** the dry run, then the upload, the same way with
   `dist\acme_api-0.5.0*`.
9. **Tag:** not created. The repository tags members as `<member>-v<x.y.z>`
   (git skill); `api-v0.5.0` and `core-v1.2.0` are the person's to push,
   or CI's.

## The answer

```
## Result
Released acme-core 1.2.0 and acme-api 0.5.0 to the internal index.
acme-api 0.5.0 requires acme-core<2,>=1.2, and acme-core had never been
published, so it went first (you agreed). services/api/pyproject.toml:
version 0.4.0 -> 0.5.0.

## Checked
- inspect_dist.py: acme_api-0.5.0 Requires-Dist acme-core<2,>=1.2,
  click>=8.1; built by hatchling 1.32.4.
- Fresh venv, wheel by path: `acme-api 1.10 2.20` -> `total 3.30`.
- Dry-run install from the internal index: failed before acme-core was
  published ("acme-core was not found"), resolved after.
- uv publish --index internal: "Uploading ..." for all four files.

## Not checked
- Consumers' own locks: they pick 0.5.0 up at their next `uv lock
  --upgrade-package acme-api`.

## Needs a person
- The tags api-v0.5.0 and core-v1.2.0, and the commit with the version
  bump pushed.
```
