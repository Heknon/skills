# Read a traceback

**Verdict you produce:** which exception started it, the frame that
matters, and the chain between them.

```
blocks:        <1 | chain of n: "During handling" / "direct cause" | group of n>
first:         <the first exception's type and message, copied>
raised at:     <file:line of the raising frame, and whose code: project, library, stdlib>
deepest project frame: <file:line in function>
frame that matters:    <file:line, and why: "the value was already wrong here, it came from ...">
chain:         <one line per block, oldest first: what each exception meant>
```

Seniority's `core/reading-errors.md` says read the first error and find
the deepest project frame. This file refines it for Python: the first
error is the **top** block of a chain, not the last line, and the deepest
project frame is where reading **starts**, not always where the cause
is. Real shapes, from the lab, are in `python/tracebacks.md`.

## Steps

1. **Count the blocks.** Look for these lines between tracebacks:

   | Line between blocks | Meaning |
   | --- | --- |
   | `During handling of the above exception, another exception occurred:` | the lower exception was raised inside an `except` for the upper one; often a bug in the handler |
   | `The above exception was the direct cause of the following exception:` | `raise New(...) from exc`: the lower one wraps the upper one on purpose |
   | `+ Exception Group Traceback` and `+-+---- 1 ----` | several independent exceptions, each with its own traceback |
   | none, and the last exception is a project's own error type | maybe `raise ... from None`: the cause was hidden (step 6) |

2. **Take the first exception**: the top block of a chain, or every
   numbered sub-exception of a group. The last line of the output is the
   last exception, which is often only a consequence.
3. **In that block, read the last frame**: the raising frame. Whose file
   is it? A path under the project, under `site-packages` or `.venv`, or
   under the interpreter's `lib` folder (the standard library).
4. **Find the deepest project frame**: going up from the raising frame,
   the first frame in the project's own files. That line passed something
   to the code below it. Copy its source line.
5. **Walk back to the frame that matters.** Ask of the deepest project
   frame: was the value already wrong when it arrived here? If yes, the
   cause is upstream: in the caller (the frame above), or in whatever
   produced the value (a parser, a file, a setting), which may not be in
   the traceback at all. Settle it with a probe at the boundary
   (`core/inspect.md`), not by reading alone.
   *lab (missing-key):* the deepest project frame was `report.py`, line
   5, `row["region"]`; a probe there printed the keys
   `'﻿region'`: the parser had produced the wrong key. The fix went
   in the parser.
6. **If the cause looks hidden** (a project error with no chain, raised
   in an `except`), print what is kept on the exception: `__context__`
   survives `from None` (*lab:* `exc.__cause__` was `None`,
   `exc.__suppress_context__` was `True`, and `exc.__context__` held the
   `TOMLDecodeError`). See `tools/probes.md` for the one-off command, or
   run `recipes/locals_on_error.py`, which walks the chain.
7. **If the raising frame is in a library**, read what the library
   expects from its installed source (the offline-docs skill), then go
   back to the deepest project frame: what did the project pass?

## Output that is not a traceback

| Seen | It is | Read |
| --- | --- | --- |
| `Exception in thread importer:` then a traceback, and the program goes on | a thread died; the exit code does not change | `python/threads.md` |
| `Task exception was never retrieved` | an asyncio task failed and nobody awaited it | `python/async.md` |
| `RuntimeWarning: coroutine 'save' was never awaited` | a coroutine was called without `await`; its body never ran | `python/async.md` |
| `Fatal Python error: Segmentation fault` and `Current thread ...` | a crash dump from `faulthandler` | `core/crash.md` |
| `Timeout (0:00:10)!` and `Thread 0x...` | a stack dump from `dump_traceback_later` | `core/hang.md` |
| `[Previous line repeated 996 more times]` then `RecursionError` | the same call recursing without end | the repeated frame's arguments: they never approach the stop condition |

## Never

- Never fix the last exception of a chain and stop: the first one is
  still there (*lab, chained:* fixing the handler's `AttributeError` left
  the app failing on the `JSONDecodeError` above it).
- Never read only the message line: the file and line of the deepest
  project frame decide where to look.
- Never blame the library frame that raised before checking what the
  project passed to it.
- Never read one sub-exception of a group and stop.
