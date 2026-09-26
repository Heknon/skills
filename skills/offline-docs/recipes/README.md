# Recipes

`lookup.py` is one script with seven commands for looking things up in an
installed environment. It uses only the standard library. Run it with the
project's interpreter, from the project folder, so it sees what the
project sees:

```powershell
uv run --no-sync python <skill>\recipes\lookup.py <command> <arguments>
```

`<skill>` is the folder holding `SKILL.md`. The script puts the current
folder first on `sys.path`, as `python -c` does, so it finds the
project's own packages the way the project's commands do (without that,
`where app.nightly` failed with `No module named 'app'` in the lab).
Every command below was run on CPython 3.12.14 with uv 0.12.19 on Linux,
in the eval sandboxes; the script was not run on Windows. Paths it
prints are the interpreter's own, so on Windows they read
`.venv\Lib\site-packages\...`.

| Command | Does | Imports the package? |
| --- | --- | --- |
| `pin <dist>` | interpreter, version, location, installer, editable or copy, the file each import name loads, compiled files, `py.typed`, stub files, a separate `<name>-stubs` folder; for an unknown name, `not installed` and similar names | no |
| `where <import>` | the file `import <import>` would load | no (a dotted name imports its parent packages) |
| `grep <import> <regex> [-i]` | every matching line in the package's `.py` and `.pyi` files and its `METADATA`, as `path:line: text`, then a count, or `no match for /<regex>/ in N file(s) under <folder>` | no |
| `lines <path> <start> [<end>]` | the lines, numbered; for files the editor cannot open, such as the standard library | no |
| `def <dotted.name>` | the signature, the `def` as `path:line` (or where a compiled function was compiled from), whether it is wrapped, the module file, the first docstring line | **yes**: read the module's top-level code first (`python/pydoc.md`) |
| `wheel <file> [<member>]` | lists a `.whl`, `.zip` or `.tar.gz`, or prints one member by path or name (`METADATA`, `RECORD`, `CHANGELOG.md`) | no; nothing is installed |
| `diff <old> <new>` | a unified diff of two files, two folders or two archives (wheels or sdists; `RECORD` is left out, dist-info names are matched across versions) | no |

## Outputs seen in the lab

`pin` on an editable project:

```
dist:      ledgerlib 0.1.0
install:   editable, from file:///home/user/od-lab/editable
import:    ledgerlib -> /home/user/od-lab/editable/src/ledgerlib/__init__.py (source)
```

`pin` with a stub package installed next to the library:

```
dist:      fetchkit 2.0.0
import:    fetchkit -> .../site-packages/fetchkit/__init__.py (source)
stubs:     separate stub package at .../site-packages/fetchkit-stubs
```

`pin` of a name that is not installed:

```
not installed: no distribution named 'fetchkt' for this interpreter
similar:   fetchkit
```

`grep` that finds nothing, the line a "not found" verdict cites:

```
no match for /ssl|verify|cert|context/ in 2 file(s) under .../site-packages/fetchkit
```

`def` on a Cython method (pydantic 1.10.26):

```
source:    none from inspect (TypeError); compiled from .../site-packages/pydantic/main.py:450
```

`def` on a C function with no text signature prints `signature: none
(ValueError: no signature found for builtin ...)`; read the docstring or a
stub then.

The examples in `examples/` show every command in use.

## Changing it

Keep it standard library only, and keep every command except `def` free
of imports of the package asked about. After a change, run each command
once in a project and compare with the outputs above.
