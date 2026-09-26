# The editor's tools

**What it decides:** which built-in tool to use for a lookup, and how to
use it well. Written for Zed's agent; the same ideas hold for any editor
agent with these tools.

| Tool | Use it for | Notes |
| --- | --- | --- |
| `grep` | text inside files, by regular expression | Rust regex: no lookbehind, no backreferences. Give it a file filter such as `**/*.py` when it accepts one. Patterns: `core/search-patterns.md` |
| `find_path` | files by name, by glob | `**/conftest.py`, `**/__main__.py`, `**/*settings*.py` |
| `list_directory` | what is in one folder | cheaper than guessing paths |
| `read_file` | a file, or a range of lines | read the range a search pointed at, not whole large files |
| `diagnostics` | the language server's errors and warnings, for one file or the project | an unresolved import error means the editor's Python cannot find that module: a clue for Resolve and Environment |
| `terminal` | commands: the interpreter, type checkers, git | Windows PowerShell; commands in `tools/terminal-probes.md`, `tools/type-checkers.md`, `tools/git.md` |
| `fetch`, `search_web` | the internet | not available air gapped; never rely on them |

If Sourcegraph's tools are connected, they are listed among your tools
too: `tools/sourcegraph.md`.

Which checker a `diagnostics` finding comes from, and whether CI agrees,
is the linting skill's `core/zed.md`.

## PowerShell, when you need the terminal for searching

The built-in `grep` is better. When you must search from the terminal:

```powershell
Get-ChildItem -Recurse -Filter *.py -Exclude .venv | Select-String -Pattern 'def\s+load\b'
Get-ChildItem -Recurse -Filter conftest.py | Select-Object FullName
```

`Select-String` uses .NET regular expressions and is case-insensitive
unless given `-CaseSensitive`; add it when searching Python names.
`Get-ChildItem -Exclude` only filters names, not folders deep in the
tree, so `.venv` hits may still appear: skip lines whose path contains
`\.venv\` or `\site-packages\`.

## Paths

Windows paths use `\`. Tools usually accept `/` too. When you copy a path
into a Python string, use `/` or a raw string `r'C:\path'`.
