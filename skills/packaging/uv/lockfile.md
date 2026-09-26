# Reading `uv.lock`

uv 0.12.19 writes `version = 1`, `revision = 3`. The lock is TOML; read
it, never edit it. Every example below is from a lab lock.

## The header

```toml
version = 1
revision = 3
requires-python = ">=3.12"

[manifest]                       # workspaces only
members = [
    "api",
    "core",
    "worker",
]

[manifest.dependency-groups]     # the root's own groups
dev = [{ name = "pytest", specifier = ">=8.4" }]
```

`requires-python` is the range the lock covers: in a workspace, the
highest floor of any member. `members` is the workspace as it was
locked: a member folder missing from the checkout makes `--locked` fail.

## One package

```toml
[[package]]
name = "click"
version = "8.5.0"
source = { registry = "http://127.0.0.1:8801/simple" }
sdist = { url = "...click-8.5.0.tar.gz", hash = "sha256:...", size = 382235, upload-time = "..." }
wheels = [
    { url = "...click-8.5.0-py3-none-any.whl", hash = "sha256:...", size = 125251, upload-time = "..." },
]
```

| `source` | Means |
| --- | --- |
| `{ registry = "<index url>" }` | from that index; the URL says which one |
| `{ registry = "indexes/internal" }` | a local folder index (`format = "flat"`); its wheels are `{ path = "..." }` with no hash |
| `{ editable = "." }` | the project itself, installed editable |
| `{ editable = "packages/core" }` | a workspace member or an editable path source |
| `{ virtual = "." }` | a project that is not built (`package = false`, or no `[build-system]`) |

The `wheels` list holds only the files the index had when the lock was
made: a mirror without Windows wheels gives a lock without them.

## What the project asked for

```toml
[package.metadata]
requires-dist = [
    { name = "acme-core", editable = "packages/core" },
    { name = "acme-report", specifier = ">=1.0", index = "http://127.0.0.1:8900/simple/" },
    { name = "pydantic", specifier = "<2" },
]
```

A requirement with a workspace or path source is recorded **without its
specifier**: the bound in `pyproject.toml` (`acme-core>=1.2,<2`) is not
in the lock and not checked (`core/workspaces.md`). A requirement pinned
to an index names that index.

## Questions and where the answer is

| Question | Look at |
| --- | --- |
| which version is installed for everyone | `version` under `[[package]]` `name = "<x>"` |
| which index it came from | its `source = { registry = ... }` |
| was this lock made against PyPI | the command below: any line is a lock from outside the air gap |
| who needs a package | not the lock: `uv tree --invert --package <x>` |
| does the lock match `pyproject.toml` | not by reading: `uv lock --check` |

```
Select-String -Path uv.lock -Pattern "pypi.org|pythonhosted"
```

(PowerShell 7.5 on Linux: 42 matches in a lock made against PyPI.)

## A lock from another world

Lab: a lock made on a connected machine with no index configured records
`source = { registry = "https://pypi.org/simple" }` and
`https://files.pythonhosted.org/...` file URLs. On the air-gapped side:

| Command | Result |
| --- | --- |
| `uv sync --locked`, no index configured | `dns error` fetching `files.pythonhosted.org` |
| `uv sync --locked` with `UV_DEFAULT_INDEX` = the mirror | ``The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.`` |
| `uv sync --frozen` with the mirror | still fetches the locked `files.pythonhosted.org` URLs: `dns error` |

The fix: the mirror as `[[tool.uv.index]]` with `default = true` in
`pyproject.toml`, then `uv lock` against it (lab: the same versions,
every `source` now the mirror, no `pythonhosted` left), then `uv sync
--locked` passes.

## Merge conflicts in the lock

Do not merge the text: `uv lock` on a lock with conflict markers stops
with ``error: Failed to parse `uv.lock` `` and `TOML parse error at line
25, column 9` (lab). Take either side's `uv.lock`, keep the merged
`pyproject.toml`, and run `uv lock`: it adds what the other side
required (lab: `Added rich v15.0.0`). The git skill owns the merge
itself.
