# Build and inspect: what is in the wheel

**Verdict you produce:** the file names, the metadata, and what is
missing or extra.

```
built:    dist/<name>-<version>.tar.gz, dist/<name>-<version>-<tags>.whl   (built by: <backend version>)
metadata: Name, Version, Requires-Python, each Requires-Dist, extras
files:    <the package's files>; missing: <list or none>; extra: <tests, secrets, build junk, or none>
```

## Build

```
uv build                      # sdist first, then the wheel from the sdist
uv build --wheel              # the wheel straight from the source tree
uv build --package acme-api   # one workspace member; output in the root's dist\
uv build --all-packages       # every member
uv build --clear              # empty the output folder first
```

- `uv build` building the wheel **from the sdist** is the check that
  matters: a file missing from the sdist is missing from the wheel. With
  hatchling, `artifacts` set on the wheel target only was not enough in
  the lab; the setting has to reach the sdist (`backends/hatchling.md`).
- The backend is fetched from the index at every build, per
  `[build-system] requires`; it is not in `uv.lock`. A mirror without it:
  `Failed to resolve requirements from build-system.requires` ...
  `Because hatchling was not found in the package registry`. The hatchling
  editable install `uv sync` makes needs `editables` from the mirror too
  (`editables~=0.3`, lab).
- uv_build is the exception: `uv build` and `uv sync` use uv's built-in
  copy (`backends/uv-build.md`).
- The output folder gets a `.gitignore` of `*` (lab);
  `--no-create-gitignore` skips it.
- Old files stay in `dist\` next to new ones. Use `--clear`, or name the
  exact file you inspect, install or upload.

## Inspect

```
uv run --no-project python <skill>\recipes\tools\inspect_dist.py "dist\*" --against src\acme_report
```

It prints, for each file: the metadata lines, `built by:` (the backend
and version, from the wheel's `WHEEL` file), the entry points, every
file, and, with `--against`, each source file the distribution lacks
(`MISSING ...`) or `every source file is in the distribution`. It exits 1
when a file is missing or the wheel has no Python module (`PROBLEM: the
wheel holds no Python module`). PowerShell does not expand `dist\*` for
programs; the script expands it itself.

## Read the listing

| Look for | Means |
| --- | --- |
| only `.dist-info/...` files | the backend found no package (`core/layout.md`) |
| a `MISSING` data file | the backend was not told to ship it (`core/layout.md`) |
| `tests/`, `.env`, `*.pem`, `notes/` in the sdist | the sdist ships what is in the tree and not ignored (hatchling, lab: `uv.lock` and `tests/` were in the sdist); check nothing secret is there |
| `Version: 0.1.dev1+g...` | a version from git with no tag in sight (`core/versioning.md`) |
| a `Requires-Dist` without an upper bound on a sibling | `core/member-release.md` |
| a platform tag (`cp312-cp312-win_amd64`) instead of `py3-none-any` | compiled code: out of this skill's scope, say so |
| a `.pth` file and no package | an editable wheel: never publish it |

## Never

- Never answer "what is in the wheel" from `pyproject.toml`: build it and
  list it.
- Never inspect a wheel you did not just build without saying where it
  came from; `dist\` keeps old builds.
