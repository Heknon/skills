# Probes

**What it decides:** how to write a probe that shows the truth, survives
a crash, and is easy to find and remove. Which probe to use is
`core/inspect.md`.

## A marked print

```python
import sys; print("DBG keys", sorted(row), file=sys.stderr)  # DBG
```

- **`DBG` twice**: in the output, so its lines stand out, and in a
  comment, so `git grep -n -I --untracked DBG` finds the line.
- **`repr` values, not `str`**: `print(sorted(row))` prints the list's
  repr, which showed `'﻿region'` in the lab; `print(key)` would have
  printed `region` with an invisible character in front. For one value
  write `print("DBG", repr(value), type(value).__name__, file=sys.stderr)`.
- **stderr**, because stdout sent to a file or pipe is held in a buffer
  and lost if the process crashes (*lab*, `core/reproduce.md`).
- **One line per event**, at the boundary (`core/inspect.md`). In a
  loop that runs thousands of times, print only when a condition holds
  (`if amount < 0:`), or count and print once at the end.

When stdout and stderr go to the same place, their lines can come out
of order: *lab (3.12.14, both captured by one pipe):* a probe's
`print()` to stdout appeared after a traceback printed to stderr later.
Put every probe on stderr and the order holds.

## How did the program get here

```python
import sys, traceback; traceback.print_stack(file=sys.stderr)  # DBG
```

*lab:*

```
  File "/home/user/dbg/tb/stack.py", line 14, in <module>
    handle({"id": 1})
  File "/home/user/dbg/tb/stack.py", line 11, in handle
    return save(dict(data))
  File "/home/user/dbg/tb/stack.py", line 6, in save
    traceback.print_stack(file=sys.stderr)  # DBG
```

The last frame is the probe itself; the ones above are the callers.

## Probes that edit nothing

- **Call the function**: `uv run python -c "from shop.shipping import order_total; print(repr(order_total([12.50, 37.50])))"`
  printed `50.0` (*lab*): the float sum was exact, a hypothesis ruled
  out without touching the code.
- **Print what `from None` hid**, with a throw-away script written from
  PowerShell (*lab: PowerShell 7.4 on Linux*, not run on Windows):

  ```powershell
  @'
  import traceback
  from svc.config import load
  try:
      load()
  except Exception as exc:
      print("cause:", repr(exc.__cause__), "suppressed:", exc.__suppress_context__)
      traceback.print_exception(exc.__context__)
  '@ | Set-Content probe_context.py
  uv run python probe_context.py
  Remove-Item probe_context.py
  ```

  It printed the hidden `TOMLDecodeError` traceback and
  `cause: None suppressed: True`. A here-string (`@'` ... `'@`, each
  marker alone on its line) keeps the Python quotes intact; write it in
  the project root so the import works, and delete it after.
- **Locals at the failure**: `uv run python recipes/locals_on_error.py
  -m sales data/may.csv` (*lab:* showed `row = {'amount': 99.0,
  'customer': 'Acme', '﻿region': 'North'}` in `totals_by_region`).

## PowerShell quoting for `python -c`

Put the Python code in double quotes and use only single quotes inside
it (navigation's `tools/terminal-probes.md` has more). For anything
with `try`, loops or several lines, use the here-string script above
instead of `-c`.

## Never

- Never probe with `print(x)` where `x` may be a string with invisible
  characters, a float, or `None` next to `"None"`: use `repr`.
- Never leave a probe file (`probe_*.py`) or a probe line behind.
