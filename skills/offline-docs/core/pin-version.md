# Pin the version first

**Verdict you produce:** which interpreter runs, which distribution and
version is installed for it, and where its files are. Nothing is read
before this, because everything read after it is only true for this
version.

```
interpreter: <path of python.exe>, Python <x.y.z>
dist:        <distribution> <version>
location:    <site-packages folder>
installed:   <a copy from an index | editable from <folder> | from <file or url>>
imports:     <import name> -> <file it loads> (<source | compiled>)
```

## Which interpreter

Which interpreter runs the project is navigation's question (its
`core/environment.md`). In a uv project (a `uv.lock`, or `[tool.uv]` in
`pyproject.toml`) one probe here is enough; for poetry, conda, pipenv, a
`python` that is not the project's, or anything unusual, answer
navigation's Environment question first and come back with the
interpreter's path.

## Steps

1. **Run the recipe** from the project folder (`recipes/README.md`):

   ```powershell
   uv run --no-sync python <skill>\recipes\lookup.py pin pydantic
   ```

   Lab output (Linux, uv 0.12.19, CPython 3.12.14; on Windows the paths
   read `.venv\Scripts\python.exe` and `.venv\Lib\site-packages`):

   ```
   python:    3.12.14 at /home/user/od-lab/old-pydantic/.venv/bin/python
   dist:      pydantic 1.10.26
   location:  /home/user/od-lab/old-pydantic/.venv/lib/python3.12/site-packages
   installer: uv
   install:   a copy from an index (no direct_url.json)
   import:    pydantic -> .../site-packages/pydantic/__init__.cpython-312-x86_64-linux-gnu.so (compiled; its .py source is beside it)
   compiled:  25 file(s) in the package, such as env_settings.cpython-312-x86_64-linux-gnu.so
   typed:     pydantic ships py.typed
   ```

   It reads metadata and asks where the import would load from; it does
   not import the package.

2. **Without the recipe**, the same facts one at a time:

   ```powershell
   uv run --no-sync python -c "import sys, platform; print(sys.executable, platform.python_version())"
   uv run --no-sync python -c "import importlib.metadata as md; print(md.version('pydantic'))"
   uv run --no-sync python -c "import importlib.util as u; print(u.find_spec('pydantic').origin)"
   uv pip show pydantic
   ```

   `uv pip show` prints `Name`, `Version`, `Location`, `Requires`,
   `Required-by`, and for an editable install `Editable project
   location` (*lab*, uv 0.12.19).

3. **Name the distribution and the import name apart.** They often differ
   (`types-fetchkit` installs `fetchkit-stubs`; `pyyaml` is imported as
   `yaml`). `python/metadata.md` maps one to the other.

4. **Check that what you will read is what runs.** The `imports:` line is
   the file the interpreter loads. A copy of the library elsewhere, such
   as `third_party\fetchkit\` in the repository, another project's
   `.venv`, or a checkout, is not it (*lab*, eval `vendored-copy`: the
   repository held 1.2.0 with `timeout=30`, the interpreter loaded 2.0.0
   from `site-packages`).

5. **Write the pin down** in the answer's `Checked:` line before reading
   any code.

## What the install kind tells you

| Seen | Meaning (*lab*, uv 0.12.19) |
| --- | --- |
| no `direct_url.json` in the `.dist-info` folder | a copy installed from an index (the mirror) |
| `direct_url.json` with `"dir_info": {"editable": true}` | editable: the code is read from the folder in `url`; `uv pip show` adds `Editable project location` |
| `direct_url.json` with another `url` | installed from that file or folder, as a copy |
| `INSTALLER` holds `uv` | uv installed it; `uv_cache.json` sits beside it |

An editable install's metadata can be stale: after the version in
`pyproject.toml` went from 0.1.0 to 0.2.0, `uv run --no-sync` still
reported `0.1.0` from `importlib.metadata`; a plain `uv run` rebuilt the
package and then reported `0.2.0` (*lab*). For an editable package, read
the version in its `pyproject.toml` too, and say which one you give.

## Not installed

`importlib.metadata.version('x')` raises `PackageNotFoundError`. The
recipe prints `not installed: no distribution named 'fetchkt' for this
interpreter` and similar names (*lab*: `similar: fetchkit`). Say which
interpreter you asked. Never install it to find out; that changes the
environment and fails air gapped.

## Never

- Never read library code before pinning its version.
- Never answer from the version you remember; say the installed one, and
  if memory disagrees, the installed one wins.
- Never pin with a bare `python` or `pip`; use `uv run --no-sync` and
  `uv pip` (seniority's team conventions).
