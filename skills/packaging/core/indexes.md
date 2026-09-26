# Indexes: the mirror, the internal index, and where each package came from

**Verdict you produce:** the index tables, and the index each package
was taken from.

```
indexes:  mirror   <url>  default = true
          internal <url>  explicit = true   publish-url = <url>
sources:  <each internal package> = { index = "internal" }
lock:     <package> <version> source = { registry = "<url>" }, one line per internal package
```

Recipe: `recipes/internal-index/`. Credentials, the CA and variables:
`uv/config.md`. Deployment's `gitlab/python.md` has the CI side (the job
token, CI/CD variables); the meaning of these tables is here.

## The shape (uv 0.12.19)

```toml
[tool.uv.sources]
acme-report = { index = "internal" }      # one line per internal package

[[tool.uv.index]]
name = "internal"
url = "https://gitlab.example.com/api/v4/groups/12/-/packages/pypi/simple"
publish-url = "https://gitlab.example.com/api/v4/projects/34/packages/pypi"
explicit = true

[[tool.uv.index]]
name = "mirror"
url = "https://pypi-mirror.example.com/simple"
default = true
```

| Key | Does (lab) |
| --- | --- |
| `name` | names the index for `[tool.uv.sources]`, `uv add --index`, `uv publish --index` and the credential variables `UV_INDEX_<NAME>_USERNAME` (`acme-internal` becomes `UV_INDEX_ACME_INTERNAL_USERNAME`) |
| `default = true` | the index of last resort, searched after every other even when its table comes first; replaces PyPI |
| `explicit = true` | used only for packages whose source names it; with no source line, acme-utils came from the mirror |
| `publish-url` | where `uv publish --index <name>` uploads; the `url` is then used to skip files already there |
| `format = "flat"` | the URL is a folder or page of files, not a simple index (a local folder of wheels works: `url = "indexes/internal"`) |

Tables are read in order. Without `index-strategy`, uv takes each package
from the **first** index that has the name at all (`first-index`).

## Dependency confusion

The same name on the mirror and on the internal index. Lab: internal
`acme-utils` 1.3.0 and 1.4.0, the mirror a public `acme-utils` 9.0.0.

| Configuration | Locked |
| --- | --- |
| both indexes, `index-strategy = "unsafe-best-match"` | **9.0.0 from the mirror**: every index is searched and the highest version wins |
| both indexes, default strategy, internal first | 1.4.0 from internal |
| both indexes, default strategy, internal index lacks the name (not yet published, a typo, an outage) | **9.0.0 from the mirror**, silently |
| internal `explicit = true` and `acme-utils = { index = "internal" }` | 1.4.0; with the name missing internally the lock **fails** (`acme-utils was not found in the package registry`) instead of taking the public one |

So: every internal package is pinned to the explicit internal index by a
source line, and no `unsafe-*` strategy is set. After fixing the tables,
relock the package (`uv lock --upgrade-package acme-utils`): removing
only the strategy left 9.0.0 in the lock (lab), because uv keeps a locked
version that still fits.

A package taken from the wrong index was downloaded, and maybe run.
Report it as a security matter; do not import it to see what it does.

## Which index did a package come from?

`uv.lock`: each package's `source = { registry = "<url>" }`
(`uv/lockfile.md`). `Select-String -Path uv.lock -Pattern 'registry = '`
lists them.

## Settings that are not in `pyproject.toml`

`UV_DEFAULT_INDEX`, `UV_INDEX` and a user `uv.toml` also add indexes.
A project's own `default = true` index won over a user `uv.toml` index in
the lab; `UV_DEFAULT_INDEX` replaced the project's default for `uv
build`, and made `uv sync --locked` fail against a lock made with another
index (`uv/config.md`). Put the indexes in `pyproject.toml`, so every
machine and CI resolve from the same place and the lock records it.

## Never

- Never set `index-strategy = "unsafe-best-match"` or
  `"unsafe-first-match"`, or add an internal index as a plain extra
  index, to make an internal package resolve.
- Never put a user name, password or token in `url`; uv keeps it out of
  `uv.lock` (lab) but `pyproject.toml` is committed.
- Never mis-spell a key: uv ignores unknown keys inside an index table
  without a warning (lab: `explicitt = true` was accepted, and the index
  was not explicit).
