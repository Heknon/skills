---
name: debugging
description: Find and fix the cause of any bug in Python code with a fixed loop - reproduce it, shrink it, test one hypothesis at a time, fix the cause, and prove the fix by reverting it. Use when asked to fix a bug, debug, find why something fails, crashes, hangs, freezes, deadlocks, leaks or grows memory, gives wrong results, fails only sometimes (intermittent, race), works on one machine but not another (works on my machine, only in CI, only on Windows), or broke after a change (regression, which commit). Also to read or explain a traceback or exception (chained, from None, ExceptionGroup, asyncio, threads), and to see values at runtime without an IDE debugger (probes, logging, pdb without a keyboard, faulthandler, tracemalloc, py-spy). Verified on Python 3.12, with 3.13 and 3.14 differences.
---

# Debugging

This skill knows the loop that finds a bug's cause, how to read what
Python prints when something goes wrong, and which tools show a running
program from a terminal with no debugger window. Every command, flag,
message and exit code in it was run on Python 3.12.14 (and 3.13.15,
3.14.7 where they differ), git 2.43.0, PowerShell 7.4 and uv 0.12.19;
Windows-only facts are marked *not run on Windows*. Nothing is written
from memory: find it here, or ask the interpreter.

Read this file, then load only what the task needs. Seniority is loaded
too: its hypothesis loop (`core/hypothesis-loop.md`) is the heart of step
5 of `core/loop.md`, and this skill does not repeat it.

## Check the versions first

```powershell
uv run python -VV                       # Python 3.12.14 (main, ...)
uv run python -c "import locale, sys; print(locale.getencoding(), sys.flags.utf8_mode)"
git --version
```

`python/versions.md` says what a debugger sees change in 3.13 and 3.14.

## The kinds of task

Every kind runs inside `core/loop.md`; the file named is where it
enters.

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Fix** | find and fix a bug from a report or a symptom | `core/loop.md`, `core/reproduce.md`, `core/prove-the-fix.md` |
| **Reproduce** | make a reported bug happen on demand | `core/reproduce.md`, `recipes/repro_template.py` |
| **Shrink** | cut a large failing case down | `core/shrink.md` |
| **Read** | explain a traceback or an error message | `core/read-traceback.md`, `python/tracebacks.md` |
| **Inspect** | see a value or a path at runtime | `core/inspect.md`, `tools/probes.md`, `tools/pdb.md` |
| **Regression** | it worked at an older version or commit | `core/regression.md` |
| **Differ** | works here, fails there | `core/differ.md`, `python/encoding.md` |
| **Intermittent** | fails sometimes, or stops failing when watched | `core/intermittent.md`, `python/threads.md` |
| **Hang** | hangs, freezes, deadlocks | `core/hang.md`, `recipes/watchdog.py` |
| **Crash** | the process dies with no Python traceback | `core/crash.md`, `tools/faulthandler.md` |
| **Memory** | memory keeps growing | `core/memory.md`, `recipes/mem_diff.py` |

A failing test, a failing pipeline or pod, and missing telemetry start
in other skills: `core/handoff.md` says which and what passes between.

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the loop and one procedure per kind, each ending in a verdict; `handoff.md` for the boundaries |
| `python/` | real traceback shapes (`tracebacks.md`), asyncio (`async.md`), threads (`threads.md`), text encoding (`encoding.md`), 3.12 to 3.14 differences (`versions.md`) |
| `tools/` | probes, pdb without a keyboard, faulthandler, logging as a probe, tracemalloc, py-spy (optional), PowerShell for runs |
| `recipes/` | scripts that ran: `repro_template.py` (exit 0/1/125, works with `git bisect run`), `watchdog.py` (stack dump at a time limit), `locals_on_error.py` (post-mortem with no prompt), `mem_diff.py` (two snapshots), `run_n.ps1` (N runs with a time limit) |
| `examples/` | finished tasks: the symptom is not the cause (`symptom-vs-cause.md`), works here, fails there (`works-here-fails-there.md`), a deadlock (`deadlock.md`), a fix that was not proven (`not-proven.md`) |

`glossary.md` fixes the words. A recipe is copied and changed only where
its top comment says.

## Invariants

1. **No edit before a reproduction has failed in front of you.** One
   command, its result copied.
2. **One change between runs.** Two changes and a passing run prove
   nothing about either.
3. **A fix is proven only by the same reproduction failing with the fix
   reverted** and passing with it (`core/prove-the-fix.md`).
4. **Fix the cause, not the line that raised.** Read the whole traceback;
   the first exception of a chain and every exception of a group.
5. **Never silence an exception to pass.** No `except: pass`, no broad
   `except` that returns `None`, no `.get()` default that hides a missing
   key; a handled error is still reported.
6. **Nothing may wait for the keyboard.** `PYTHONBREAKPOINT=0`, pdb only
   in the forms `tools/pdb.md` lists, and a time limit with a stack dump
   on anything that may hang.
7. **Timing is not fixed with time.** No `sleep`, longer timeout or retry
   for a race or a hang; force the failure, then remove the cause.
8. **Every probe is removed** before the answer, and the search for its
   marker finds nothing.

## What you say when you finish

End with these headings, each with `none` when empty. They come before
the headings of any other loaded skill (pytest's, then seniority's).

```
## Cause
<file:line and what is wrong there; for a chain or group, each cause>

## Reproduction
<the command, and its result before the fix; a rate for an intermittent bug>

## Fix
<what changed, where, and why it removes the cause>

## Proof
<the same command with the fix, and with the fix reverted, and both results>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
