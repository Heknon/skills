# pydoc and help(): docstrings without a pager

**What it decides:** how to print a module's, class's or function's
documentation in the terminal without waiting in a pager, and what each
pydoc command imports.

All of it was run on CPython 3.12.14 (Linux). A docstring is the author's
description, rank 5 in `core/evidence.md`: a lead, checked in the code.

## help() and pydoc wait in a pager in a terminal

`pydoc.getpager` (`pydoc.py:1652`) decides. It prints straight out when
standard input or output is not a terminal (lines 1658-1659), or when
`TERM` is `dumb` or `emacs` and no `PAGER`/`MANPAGER` is set (line 1670).
Otherwise it pages: `less` on Linux, and on Windows `more <` on a
temporary file (line 1673).

Lab, in a pseudo-terminal:

| Command | Result |
| --- | --- |
| `python -m pydoc json` | stuck in `less`; killed after 5 s (exit 124) |
| `python -c "help(len)"`, also through `uv run --no-sync` | stuck; killed after 5 s |
| `TERM=dumb python -m pydoc json` | printed `Help on package json:` and returned |
| `python -m pydoc json` piped into another program | printed and returned |

Zed's agent terminal was not tested; treat it as a terminal. On Windows,
`more` waits for a key (source line 1673; not run on Windows). So in the
agent, print documentation in a way that never pages:

```powershell
uv run --no-sync python -c "import pydoc, json; print(pydoc.render_doc(json.dumps, renderer=pydoc.plaintext))"
```

```
Python Library Documentation: function dumps in module json

dumps(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None, separators=None, default=None, sort_keys=False, **kw)
    Serialize ``obj`` to a JSON formatted ``str``.
```

`pydoc.plaintext` removes the bold-by-backspace formatting. For only the
signature, file, line and first docstring line, the recipe's `def`
command is shorter. In PowerShell, `$env:TERM = 'dumb'` before `help()`
takes the line-1670 branch (not run on Windows).

## Imports run code

Every pydoc route to a module's docstring imports it, and importing runs
its top-level code. Eval `import-side-effect`: reportjob 1.0.0 ends with
`send(build([]))` (`reportjob/__init__.py:27`), which appends a line to
`reportjob-sent.log`.

| Command | Imported reportjob? (*lab*) |
| --- | --- |
| `import reportjob; pydoc.render_doc(reportjob.build, ...)` | yes: the log line appeared |
| `python -m pydoc -w reportjob` | yes |
| `python -m pydoc -k nightly` | yes, although it only searches summaries |
| `python -m pydoc modules` | yes |
| `importlib.util.find_spec('reportjob').origin`, then reading the file | no |
| `recipes/lookup.py pin`, `where`, `grep`, `lines` | no |

`-k` and `modules` import every package on `sys.path`: they walk it with
`pkgutil.walk_packages`, whose docstring says it "must import all
*packages* (NOT all modules!)" (`pkgutil.py:49-51`), to find submodules.

So before importing a module you do not know, find its file without
importing it and read its top-level code, the lines not inside a `def` or
`class`. Look for calls, connections, file writes, `main()`.

## The pydoc commands

| Command | What it did in the lab |
| --- | --- |
| `python -m pydoc <name>` | text documentation; pages in a terminal |
| `python -m pydoc -w <name>` | wrote `<name>.html` into the **current folder** and printed `wrote reportjob.html`; for a name it cannot find: `No Python documentation found for 'fetchkit'.`, exit 1 |
| `python -m pydoc -p <port>` | started a server on `localhost`, printed `Server ready at http://localhost:<port>/` and `Server commands: [b]rowser, [q]uit`, then waited at `server>` for a command |
| `python -m pydoc -p 0` with no input | printed the same, then `Server stopped` at once |
| `python -m pydoc -k <word>` | module names whose summary line matches, such as `json - JSON (JavaScript Object Notation) ...`; imports every package |
| `python -m pydoc FORMATTING`, `topics`, `keywords` | the language reference topics from `pydoc_data/topics.py` (`tools/cli-help.md`) |

`-p` is not usable from an agent: in a terminal it holds the command at
the `server>` prompt, and without input it stops before any page can be
read. While it ran, `curl http://localhost:<port>/fetchkit.html` returned
the page with `get(url, **kw)`. Windows may ask whether to allow the
server through the firewall (not run on Windows). Use `-w` when a person
wants an HTML page to open; use `render_doc` for yourself.

## Never

- Never type `help(x)` or `python -m pydoc x` in the agent's terminal.
- Never run `pydoc -k` or `pydoc modules` where a package may do work on
  import.
- Never leave a `pydoc -p` server running.
