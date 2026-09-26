# Discover: which function, class or option does this

**Verdict you produce:** the candidate names, each with its `path:line`
in the installed package, and which one does what was asked; or
`not found` with every place looked.

```
asked:      <what it should do>
candidates: <name> at <path>:<line> - <what its def or docstring says>
answer:     <the one that does it, checked in its code> | not found (<where looked>)
```

Pin the version first (`core/pin-version.md`). Know the import name
(`python/metadata.md`).

## Steps, cheapest first

1. **The public names.** `__all__` is the list the author exports; `dir()`
   shows everything the module holds.

   ```powershell
   uv run --no-sync python -c "import quickcfg as m; print(getattr(m, '__all__', None)); print([n for n in dir(m) if not n.startswith('_')])"
   ```

   ```
   ['load', 'UnsupportedFormat']
   ['UnsupportedFormat', 'load', 'loader']
   ```

   This imports the package. For a package whose top-level code you have
   not read, use step 2 first (`python/pydoc.md`, "Imports run code").

2. **Every definition in the package**, without importing it:

   ```powershell
   uv run --no-sync python <skill>\recipes\lookup.py grep quickcfg "^\s*(def|class) "
   ```

   ```
   .../quickcfg/loader.py:8: class UnsupportedFormat(ValueError):
   .../quickcfg/loader.py:12: def _read_toml(text):
   .../quickcfg/loader.py:16: def _read_json(text):
   .../quickcfg/loader.py:20: def _read_ini(text):
   .../quickcfg/loader.py:30: def load(path, *, format="auto", env_prefix=None, defaults=None):
   5 match(es) for /^\s*(def|class) / in 2 file(s) under .../site-packages/quickcfg
   ```

3. **Words from the question.** Search the package for the words a person
   would use and their synonyms, case-insensitive, one search with
   alternatives: `lookup.py grep quickcfg "yaml|yml" -i`. Search the
   `.pyi` stubs too (the recipe does), and the `METADATA` text
   (`python/metadata.md`), which often holds the README.
4. **Compiled packages** have no `def` lines. List their names with
   `dir()` (orjson 3.12.0: `dumps`, `loads`, `Fragment`, the `OPT_*`
   flags and the exception classes, *lab*) and read the stub
   (`python/stubs.md`).
5. **Many packages at once** (you do not know which package has it):
   `python -m pydoc -k <word>` searches the one-line summary of every
   module on the path; `-k json` found `json`, `json.decoder`, `orjson`
   and others (*lab*). It imports every package on the path to do so,
   which runs their top-level code (*lab*: it triggered reportjob's
   import side effect). Use it only when you cannot name the package.
6. **Read each candidate's `def`** and the lines that decide the case
   (`core/behaviour.md`). A name that sounds right is a candidate until
   its code does what was asked.

## An option is a parameter, a setting key, or a value

"Which setting makes it read YAML" can be answered by a parameter
(`format=`), by a value of a parameter (`format="yaml"`), by a key in a
config file, or by an environment variable. Look for all four: the
`def`, the dictionaries or `if` chains that check the value (quickcfg
3.1.0: `_READERS = {"toml": ..., "json": ..., "ini": ...}` at
`loader.py:26`), and `os.environ` reads (`lookup.py grep <pkg>
"environ|getenv"`).

A parameter that exists (`format=`) does not make every value valid. The
installed code decides which values are accepted.

## Not found

When nothing does it, say so, with where you looked, in the answer's
`Verdict:` line (`core/evidence.md`):

```
Verdict:  not found (quickcfg 3.1.0: load() parameters at loader.py:30; _READERS and
          _SUFFIXES at loader.py:26-27; "yaml|yml" in every .py of the package and
          in quickcfg-3.1.0.dist-info/METADATA: no match)
```

Then give the person the real choices; never invent the option.

## Never

- Never answer with a name you did not find in the installed package.
- Never stop at one search that found nothing: try the synonyms, the
  stubs, the METADATA text, and the values checked in code.
- Never run `pydoc -k` or `help('modules')` in an environment with
  packages you do not trust to import cleanly.
