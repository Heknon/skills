# Behaviour: what the code does in one case

**Verdict you produce:** the lines of installed code that decide the case
(a default, an error, what `None` means), as `path:line`, and what they
do.

```
case:    <the question, such as "retry_call called without retries">
decides: <path>:<line>  <the line>
         <path>:<line>  <the next line on the path, if any>
result:  <what happens>
```

Pin the version first (`core/pin-version.md`).

## A docstring is a lead, not an answer

The docstring, `help()`, a README or a comment says what the author meant
at some point. The code says what runs. In eval `stale-docstring`,
callagain 0.9.0's `retry_call` docstring says "By default a failing call
is retried 3 times"; the code says:

```
callagain/core.py:6       def retry_call(fn, *args, retries=None, delay=None, **kwargs):
callagain/core.py:12          if retries is None:
callagain/core.py:13              retries = DEFAULT_RETRIES
callagain/_defaults.py:3  DEFAULT_RETRIES = 0
```

A failing function passed to it was called once (`calls: 1`, *lab*).
Answer 0, and say the docstring is wrong for this version.

## Steps

1. **Find the entry point**: the function the caller calls, its `def`
   as `path:line` (`core/signature.md` step 1).
2. **Find the lines that decide the case.** For a default, the parameter's
   default, then any `if x is None:` that replaces it. For an error, the
   `raise` and the condition above it. Search inside the one package:

   ```powershell
   uv run --no-sync python <skill>\recipes\lookup.py grep callagain "DEFAULT_RETRIES|retries"
   ```

3. **Follow the value** through each call it is passed to, as in
   `core/signature.md` step 3, until a line uses it. Constants imported
   from another module (`from callagain._defaults import DEFAULT_DELAY,
   DEFAULT_RETRIES` at `core.py:3`) are followed to their assignment.
4. **Stop at the edge that answers the question.** Into the standard
   library is fine when the question needs it (below). Into compiled code
   you cannot read: say so, and use the docstring or stub as a lead, with
   the verdict "confirmed from help only".
5. **Check with a small run when it is safe**: a call that touches no
   network, file or database, such as counting calls of a function that
   raises. A run confirms one case; the lines say why.
6. **Report** the decisive lines, what they do, and where the docstring
   or memory disagreed.

## Into the standard library

The standard library's source is on the machine: the interpreter's `Lib\`
folder (Linux: `lib/python3.12/`), printed by:

```powershell
uv run --no-sync python -c "import sysconfig; print(sysconfig.get_paths()['stdlib'])"
```

It is outside the project, so read it with `recipes/lookup.py lines
<path> <start> <end>` when the editor cannot open it.

Worked in eval `vendored-copy`: fetchkit 2.0.0's `_send` passes
`timeout=None` to `urllib.request.urlopen(req, timeout=timeout)`
(`_transport.py:11`). In 3.12.14, `urlopen`'s own default is
`socket._GLOBAL_DEFAULT_TIMEOUT` (`urllib/request.py:138`), and
`socket.create_connection` sets a timeout only when it is not that default:

```
socket.py:846     if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
socket.py:847         sock.settimeout(timeout)
```

`settimeout` is compiled; its docstring says "Setting a timeout of None
disables the timeout feature". So an explicit `None` means no timeout at
all, even if `socket.setdefaulttimeout` was called. Checked with a run
against a local socket that accepts and never answers, after
`socket.setdefaulttimeout(1)`: `urlopen(url)` raised `TimeoutError` after
1.0 s; `urlopen(url, timeout=None)` was still waiting when stopped at 4 s
(*lab*).

Some standard library code you find does not run. `collections/__init__.py`
defines `class OrderedDict` at line 83 and then replaces it with the
compiled one (`from _collections import OrderedDict`, line 340);
`inspect.getsource(collections.OrderedDict)` still returns the Python
class (*lab*). `python/inspect.md` lists these.

## Never

- Never answer a behaviour question from a docstring, `help()`, a README
  or a comment alone when the code is on the machine.
- Never answer from a copy of the library that is not the one imported
  (`core/pin-version.md` step 4).
- Never change the library's files to test an idea; they are shared by
  everything in that environment.
