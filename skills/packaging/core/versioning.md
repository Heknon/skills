# Versioning: bump, or derive from git tags

**Verdict you produce:** the version the built wheel carries.

```
source:   <static in pyproject.toml | file <path> | git tags via <hatch-vcs | setuptools-scm>>
set to:   <x.y.z> by <command>
wheel:    dist/<name>-<x.y.z>-py3-none-any.whl, METADATA "Version: <x.y.z>"
tag:      <the tag it matches, or "not tagged: the person or CI tags">
```

## The default: a static version, bumped with uv

```
uv version                          # acme-report 1.2.0
uv version --bump minor --dry-run   # acme-report 1.2.0 => 1.3.0, file unchanged
uv version --bump minor             # writes 1.3.0, relocks and syncs
uv version 2.0.0rc1                 # sets an exact value
uv version --short                  # 1.3.0
uv version --package acme-core --bump major   # one workspace member
```

`--bump` takes `major`, `minor`, `patch`, `stable`, `alpha`, `beta`,
`rc`, `post`, `dev`, and can be given twice (`uv help version`,
0.12.19). `--no-sync` leaves the environment alone. The version must be
checked against the tag before a release: tags are git's to make
(`core/publish.md`).

## Versions from files and tags (dynamic)

For projects that already use them; each makes `uv version` fail with
`We cannot get or set dynamic project versions in: pyproject.toml`.

| Source | Configuration | Lab result |
| --- | --- | --- |
| a file, hatchling | `dynamic = ["version"]`, `[tool.hatch.version] path = "src/acme/core/__init__.py"` holding `__version__ = "1.1.0"` | `1.1.0`; without the line: `Error getting the version from source `regex`: unable to parse the version from the file` |
| a file, setuptools | `[tool.setuptools.dynamic] version = { attr = "ledger.__version__" }` | `0.2.0` |
| git tags, hatchling | `requires = ["hatchling", "hatch-vcs"]`, `[tool.hatch.version] source = "vcs"` | tag `v1.4.0` on HEAD: `1.4.0` |
| git tags, setuptools | `requires = ["setuptools", "setuptools-scm"]`, `[tool.setuptools_scm]` (optionally `version_file = "src/ledger/_version.py"`) | tag `v2.3.0` on HEAD: `2.3.0` |

What a tag-derived version looks like (hatch-vcs 0.5.0, setuptools-scm
10.3.4, lab):

| The checkout | Version |
| --- | --- |
| HEAD is the commit tagged `v1.4.0` | `1.4.0` |
| one commit after the tag | `1.4.1.dev1+gd109709b9` |
| a tracked file changed, not committed | `2.3.1.dev0+g5f278aa27.d20260926` (an untracked file does not count) |
| **no tag visible** (`git clone --depth 1 --no-tags`) | `0.1.dev1+gd109709b9`, with a `UserWarning: "<path>" is shallow and may cause errors` |
| no `.git` folder at all (a copied tree) | the build fails: `LookupError: Error getting the version from source `vcs`: setuptools-scm was unable to detect version for <path>` |

## When the wheel says `0.1.dev1`

The tags are not in the clone.

1. `git describe --tags` in the same checkout: `fatal: No tags can
   describe '<sha>'` confirms it; `git tag` lists nothing.
2. If HEAD is the tagged commit: `git fetch --tags` is enough (lab: then
   `1.4.1`). If HEAD is later than the tag in a shallow clone, fetching
   the tag is not enough (`No tags can describe`); `git fetch --tags
   --unshallow` is (lab: then `1.4.1.dev1+g...`).
3. Rebuild and read the file name. In CI the fetch depth is a job
   setting: the deployment skill owns it.
4. `SETUPTOOLS_SCM_PRETEND_VERSION=1.4.0` forces a version (lab: the
   error message names it and `VCS_VERSIONING_PRETEND_VERSION`); use it
   only from the tag's own name in CI, never as a fixed value in a file.

## Never

- Never report the version you set; report the one in the built file's
  name and METADATA.
- Never bump a version that is already published to change it back: a
  version cannot be uploaded twice, so the next one is the fix.
- Never move a project from a static to a tag-derived version, or back,
  unasked.
