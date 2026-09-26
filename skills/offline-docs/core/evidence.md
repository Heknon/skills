# Evidence: which source wins, and how to say "not found"

**Verdict you produce:** the answer block below, for every question
answered. Its last line is one of three verdicts.

```
Answer:   <one or two lines>
Checked:  <distribution> <version>, Python <x.y.z>, <interpreter path>
Evidence: <path:line and what is there> | <command and the line it printed>
Source:   code | stub | docstring | --help | metadata | internal page
Verdict:  confirmed from source at <path:line> on <dist> <version>
          | confirmed from <stub | help | page> only (<which, and its version>)
          | not found (<every place looked>)
```

## Ranking of sources

When two disagree, the higher one wins, and the answer says they
disagree.

| Rank | Source | Why it ranks here |
| --- | --- | --- |
| 1 | the installed code that runs, read at `path:line` in `site-packages` or the interpreter's `Lib\` | it is what executes, for this version |
| 2 | a run of the call, in this environment | shows one case; the code says why |
| 3 | a stub (`.pyi`) shipped with the package | written by the authors for this version, but only signatures |
| 4 | a separate stub (`types-*`, a checker's bundled typeshed) | may be for another version (`python/stubs.md`) |
| 5 | the docstring, `help()`, the `METADATA` text, a tool's `--help` | the author's words; can be stale (eval `stale-docstring`) |
| 6 | an internal page | may describe another version (`core/docs.md`) |
| - | memory, a blog post you remember, another project's copy | never evidence; only a hint of where to look |

A tool written in another language (ruff, uv, ty) has no readable source
on the machine; its own output is the best evidence there is
(`core/tool.md`).

## The three verdicts, from the lab

**Confirmed from source.** The code was read at the line that decides:

```
Verdict:  confirmed from source at .venv/lib/python3.12/site-packages/pydantic/main.py:450
          on pydantic 1.10.26
```

For a compiled module whose `.py` source is shipped beside it (pydantic
1.10.26 ships `main.py` next to `main.cpython-312-x86_64-linux-gnu.so`;
the Windows wheel has `main.cp312-win_amd64.pyd`), the `.py` counts as
source: both are listed in the same wheel's `RECORD`, and the compiled
function's `__code__.co_filename` names `pydantic/main.py` line 450, the
line of `def dict(` (*lab*).

**Confirmed from a stub, help or page only.** There was no source to read,
or you did not read it:

```
Verdict:  confirmed from stub only (orjson/__init__.pyi:10-14, shipped in orjson 3.12.0),
          with METADATA lines 166-168 and a run of the call
```

**Not found.** Nothing in the installed version does it. Name every place
looked, so the person can see the search was complete:

```
Verdict:  not found (fetchkit 2.0.0: get(url, **kw) at __init__.py:9 passes **kw to
          _send at _transport.py:7, which takes body, query, headers, timeout;
          "ssl|verify|cert|context" in every .py of the package: no match)
```

## Writing "not found"

"Not found" is a complete answer, not a failure. Before writing it:

1. Search the right version (the pin).
2. Search the whole package, not one file: the recipe's `grep` covers
   every `.py`, `.pyi` and the `METADATA`.
3. Search for the synonyms a person would use, in one pattern
   (`yaml|yml`, `ssl|verify|cert`).
4. Follow `**kwargs` to where they land (`core/signature.md`).
5. For an option: parameters, accepted values, config keys, environment
   variables (`core/discover.md`).

Then list those places in the verdict. After it, give the real choices
(another function that exists, a change the person could make, a question
for whoever owns the library), each marked as a suggestion.

## Never

- Never give an answer without the `Checked:` line; an answer without a
  version is memory.
- Never write "confirmed from source" for a line you did not read in the
  installed file.
- Never fill a gap with a guess: an option, flag, parameter or changelog
  entry you did not find does not go in the answer, even as "probably".
