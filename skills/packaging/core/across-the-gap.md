# Across the gap: bring packages in, or build a wheelhouse

**Verdict you produce:** the export, the script for the connected side,
the check for the target platform, and an offline install that passed.

```
export:     uv export ... -o requirements.txt  (<n> packages, hashes)
connected:  fetch-wheels.sh for <platform>, Python <x.y>   (run by <person>)
checked:    uv pip compile ... --python-platform <target> --no-index --find-links wheelhouse -> resolves
offline:    uv pip install --offline --no-index --find-links wheelhouse -r requirements.txt -> "+ <packages>"
```

You work on the air-gapped side. The connected side is a person running
a script you write (`recipes/wheelhouse/`). Git bundles are the git
skill's; this is about Python packages.

## Is a wheelhouse the right answer?

Usually the missing package belongs **on the mirror**: ask whoever runs
it to add it, and nothing else changes. A wheelhouse is for a machine
with no mirror at all, or for bringing a set of wheels to the mirror's
administrator.

## Steps

1. **Export what the lock says**, on the air-gapped side:
   ```
   uv export --no-emit-project --no-dev -o requirements.txt
   ```
   Pinned versions with `--hash` lines for every file the lock knows.
   Workspace: `--package <member>` and `--no-emit-workspace` leave the
   siblings out (they are built, not downloaded). uv 0.12.19 has no `uv
   pip download` (`unrecognized subcommand 'download'`).
2. **Write the connected side's script** from
   `recipes/wheelhouse/fetch-wheels.sh`: `pip download -r
   requirements.txt -d wheelhouse --only-binary=:all: --platform
   <tag> --python-version 3.12 --implementation cp`. Without
   `--platform`, pip fetches wheels for the machine it runs on: Linux
   wheels for a Windows target (the failure below). Add the build backend
   (`hatchling==1.32.4`) if the project is built on the far side.
   The hashes in the export made pip check each file (lab: pip 26.2.1
   accepted them with `--platform`).
3. **Check the wheelhouse for the target before it crosses**, anywhere uv
   runs:
   ```
   uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.12 --no-index --find-links wheelhouse --offline
   ```
   It resolves, or names the package without a matching wheel.
4. **Install offline** on the far side, into a venv:
   ```
   uv venv .venv --python 3.12
   uv pip install --offline --no-index --find-links wheelhouse -r requirements.txt
   uv build --offline --no-index --find-links wheelhouse
   uv pip install --offline --no-index --no-deps dist\reporter-1.0.0-py3-none-any.whl
   ```
   Lab (Linux, network cut): all four passed and `import reporter,
   pydantic` worked. Not run on Windows.

## Platform tags

| Target | `--platform` for pip | `--python-platform` for uv |
| --- | --- | --- |
| Windows, 64-bit | `win_amd64` | `x86_64-pc-windows-msvc` |
| Linux, x86-64 (glibc) | `manylinux_2_17_x86_64` | `x86_64-unknown-linux-gnu` |

Pure-Python wheels (`py3-none-any`) fit every target. One wheelhouse can
hold both platforms: run the script once per platform (lab).

## When the offline install fails on the target

Lab, a Linux wheelhouse installed for Windows:

```
error: No solution found when resolving dependencies
  cause: Because pydantic-core==2.46.5 has no wheels with a matching platform tag (e.g., `win_amd64`) and you require pydantic-core==2.46.5, we can conclude that your requirements are unsatisfiable.

hint: Wheels are available for `pydantic-core` (v2.46.5) on the following platforms: `manylinux_2_17_x86_64`, `manylinux2014_x86_64`
```

The hint names the platforms the wheelhouse has. Fix the download
(step 2), check (step 3), carry it again.

## A uv project with a lock, offline

`uv sync` cannot use a wheelhouse for a lock made against an index: with
`--offline --find-links wheelhouse` it looked for the locked URLs in the
cache (`Network connectivity is disabled, but the requested data wasn't
found in the cache`), and with `--no-index` the lock no longer matched.
Use `uv pip install` from the exported requirements as above, or get the
packages onto the mirror.

## Never

- Never download sdists for the target (`--only-binary=:all:`): they
  need a compiler and headers the far side may not have.
- Never change a version in `requirements.txt` to one the wheelhouse
  happens to have; export again from the lock.
