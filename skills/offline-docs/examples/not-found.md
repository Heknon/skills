# Worked example: the option does not exist

Kinds: Discover, Behaviour. Verdict: not found. Commands and output from
a lab run of eval `no-such-option` (Linux, uv 0.12.19, CPython 3.12.14);
`.../site-packages` stands for
`/home/user/od-lab/ex3/.venv/lib/python3.12/site-packages`.

## The ask

> Which quickcfg setting makes it read our `settings.yaml` instead of
> `settings.toml`?

The question assumes the setting exists. `load()` has a `format=`
parameter, which makes `format="yaml"` look plausible. Find out before
answering.

## Steps

1. **Pin**:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py pin quickcfg
   python:    3.12.14 at /home/user/od-lab/ex3/.venv/bin/python
   dist:      quickcfg 3.1.0
   ...
   import:    quickcfg -> .../site-packages/quickcfg/__init__.py (source)
   ```

2. **Search for the words**, case-insensitive, both spellings
   (`core/discover.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py grep quickcfg "yaml|yml" -i
   no match for /yaml|yml/ in 3 file(s) under .../site-packages/quickcfg and its METADATA
   ```

   One empty search is not yet "not found" (`core/evidence.md`).

3. **List every definition, the format tables and environment reads**:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py grep quickcfg "^\s*(def|class) |environ|_READERS|_SUFFIXES"
   .../quickcfg/loader.py:8: class UnsupportedFormat(ValueError):
   .../quickcfg/loader.py:12: def _read_toml(text):
   .../quickcfg/loader.py:16: def _read_json(text):
   .../quickcfg/loader.py:20: def _read_ini(text):
   .../quickcfg/loader.py:26: _READERS = {"toml": _read_toml, "json": _read_json, "ini": _read_ini}
   .../quickcfg/loader.py:27: _SUFFIXES = {".toml": "toml", ".json": "json", ".ini": "ini", ".cfg": "ini"}
   .../quickcfg/loader.py:30: def load(path, *, format="auto", env_prefix=None, defaults=None):
   ...
   .../quickcfg/loader.py:48: for name, value in os.environ.items():
   14 match(es) for /^\s*(def|class) |environ|_READERS|_SUFFIXES/ in 3 file(s) under .../site-packages/quickcfg and its METADATA
   ```

4. **Read the lines that decide** (`core/behaviour.md`):

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py lines .../site-packages/quickcfg/loader.py 36 41
      36      path = Path(path)
      37      if format == "auto":
      38          format = _SUFFIXES.get(path.suffix.lower(), path.suffix)
      39      try:
      40          reader = _READERS[format]
      41      except KeyError:
   ```

   Whatever `format` is, the reader comes from `_READERS`, which has
   `toml`, `json` and `ini`. The environment is read only for values
   under `env_prefix` (line 48), not for the format.

5. **Confirm with a safe run** (it only reads a local file):

   ```
   > uv run --no-sync python -c "import quickcfg; quickcfg.load('settings.yaml')"
   quickcfg.loader.UnsupportedFormat: cannot read '.yaml'; known formats: ini, json, toml
   ```

   And no YAML library is installed: `import yaml` gave
   `ModuleNotFoundError: No module named 'yaml'`; `uv pip list` shows only
   `quickcfg 3.1.0`.

## The answer

```
## Answer
Answer:   No setting does it: quickcfg 3.1.0 reads TOML, JSON and INI only.
          format= exists but accepts only those. Choices for you: convert
          settings.yaml to TOML (settings.toml already holds the same keys), or
          add a YAML reader, which needs a YAML library this environment lacks.
Checked:  quickcfg 3.1.0, Python 3.12.14, /home/user/od-lab/ex3/.venv/bin/python
Evidence: loader.py:26 _READERS = {"toml", "json", "ini"}; loader.py:40 reader =
          _READERS[format]; run: UnsupportedFormat: cannot read '.yaml'; known
          formats: ini, json, toml
Source:   code
Verdict:  not found (quickcfg 3.1.0: load() parameters at loader.py:30; _READERS and
          _SUFFIXES at loader.py:26-27; environment reads at loader.py:48;
          "yaml|yml" in every .py of the package and its METADATA: no match)

## Not checked
- Other quickcfg versions: not on this machine.
```
