# uv 0.8 and 0.12

Check first: `uv --version`. This skill is written for uv 0.12.19, the
version deployment's images use. The plan for this skill was drafted on
uv 0.8.17; both were run side by side in the lab, and this is what
differed for the commands here.

| Topic | 0.8.17 | 0.12.19 |
| --- | --- | --- |
| `uv workspace list`, `uv workspace dir`, `uv workspace metadata` | missing | present (`metadata` warns it is experimental) |
| `uv build --clear`, `--no-create-gitignore` | missing | present |
| system certificates | `--native-tls`, `UV_NATIVE_TLS` | `--system-certs`, `UV_SYSTEM_CERTS`; `UV_NATIVE_TLS` still works and warns it is deprecated |
| `uv publish --dry-run` with no URL | checked the files against `https://upload.pypi.org/legacy/`; nothing sent | the same, and it **also tried to fetch a trusted publishing token from `upload.pypi.org`** (network) |
| `uv init --package` backend | `uv_build>=0.8.17,<0.9.0` | `uv_build>=0.12.19,<0.13.0` |
| `uv audit`, `uv check` | missing | present (dependency audit and type checks: not this skill's) |

The same on both (lab):

- `uv auth login/logout/token/dir`, `uv version --bump`, `uv lock
  --check`, `uv add --bounds` (preview), `uv build --package` and
  `--all-packages`; no `uv pip download` on either.
- The missing workspace source error, word for word:
  `` `acme-core` is included as a workspace member, but is missing an
  entry in `tool.uv.sources` (e.g., `acme-core = { workspace = true }`) ``.
- The workspace lock drops the bound on a workspace source
  (`{ name = "acme-core", editable = "packages/core" }`), so a library
  bumped past its dependents' bounds still locks.
- The output folder of `uv build` gets a `.gitignore` of `*`.

## The plan's monorepo facts, rechecked on 0.12.19

Each held: one lock at the root; the missing-source error; a bare sibling
published as `Requires-Dist: acme-core` and a bounded one as
`Requires-Dist: acme-core<2,>=1.2`; `uv sync --package` installing one
member and its siblings; `uv build --package` building one member;
`uv lock` from a member folder writing the root lock; the lock's
`requires-python` being the strictest member's; `uv lock --locked`
failing on a stale lock. One was added: the lock does not check sibling
bounds at all (`core/workspaces.md`).

## A lock written by another uv

Both write `version = 1` and `revision = 3` at the top of `uv.lock`.
Reading one version's lock with the other was not tried; when machines
run different uv versions, pin uv with `required-version`
(`uv/config.md`) so the lock is always written by the same one.
