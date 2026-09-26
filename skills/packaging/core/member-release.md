# Member release: build, version or publish one member

**Verdict you produce:** the member's wheel, its published requirements
on siblings, the tag, and the dependents checked.

```
member:     <distribution> <version>   (uv version --package <name> --short)
wheel:      dist/<name>-<version>-py3-none-any.whl
siblings:   Requires-Dist: <sibling><bound>, each bounded; each sibling version on the index: <yes | needs releasing first>
dependents: <member>: <its bound on this member> -> <ok | breaks>
tag:        <member>-v<version> (or the repository's convention), made by <the person | CI>
```

## Steps

1. **Version.** `uv version --package acme-api --short`; bump with
   `uv version --package acme-api --bump minor` if the release needs it
   (`core/versioning.md`). One member, one version; the others do not move.
2. **Build that member only:** `uv build --package acme-api`. The files
   land in the root's `dist\`; name them exactly afterwards, since other
   members' builds sit there too.
3. **Read its sibling requirements:**
   `uv run --no-project python <skill>\recipes\tools\inspect_dist.py dist\acme_api-0.4.0-py3-none-any.whl`.
   Every `Requires-Dist` on a sibling must have a bound. A bare
   `Requires-Dist: acme-core` accepts any acme-core ever published: bound
   it in `pyproject.toml` from what the member uses (`>=` the version
   whose features it needs, `<` the next major), rebuild, read again
   (lab: `Requires-Dist: acme-core<2,>=1.2`).
4. **The siblings must be installable too.** A published acme-api needs
   a published acme-core inside its bound. Check both together, the way
   an installer will see them:
   ```
   uv build --all-packages
   uv venv $env:TEMP\release-check --clear
   uv pip install --python $env:TEMP\release-check\Scripts\python.exe --dry-run --find-links dist acme-api
   ```
   (lab on Linux, `bin/python`: `+ acme-api==0.4.0`, `+ acme-core==1.2.0`
   ... ). If the sibling's version is not on the internal index yet, it
   is released first.
5. **Tag** in the repository's convention: the git skill owns the naming
   (such as `api-v0.4.0`); a tag per member keeps each member's release
   apart. Create it only when asked.
6. **Publish**: `core/publish.md`. In CI, deployment's publish component
   takes the member name as its `package` input.

## Releasing a library that others use (a major version)

`uv lock` will not warn you: the workspace source replaces the bound in
development (`core/workspaces.md`). Lab: acme-core bumped to 2.0.0,
`uv lock` passed, while acme-api said `acme-core>=1.4,<2`.

1. Find every dependent and its bound, and every use of what changes:
   ```
   git grep -n "acme-core" -- "*pyproject.toml"
   git grep -n "legacy_total" -- "*.py"
   ```
2. Show the clash from built wheels: after the bump, `uv build
   --all-packages`, then the dry run above for each dependent. Lab:
   ```
   cause: Because only acme-core==2.0.0 is available and all versions of acme-api depend on acme-core>=1.4,<2, we can conclude that all versions of acme-api cannot be used.
   ```
   A dependent with no upper bound (`acme-core>=1.0`) resolves and breaks
   at import instead: read its code for the removed names.
3. Report each dependent with what it needs (a new bound, a code change,
   a release). Changing a dependent's bound or code is a separate change:
   ask before making it.

## Never

- Never publish a member whose sibling requirement has no upper bound.
- Never bump a library's major version and tag it before every
  dependent is read.
- Never build or publish the whole workspace to release one member.
