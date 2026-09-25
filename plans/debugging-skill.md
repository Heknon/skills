# Plan: the debugging skill

Status: draft for decision. Nothing is built yet.

## 1. What it is

A fixed loop for any bug in Python code: reproduce it, shrink it to a
minimal case, form one hypothesis, test it, fix the cause, and prove the
fix: the reproduction now passes, and fails again with the fix reverted.
Around the loop, the knowledge a weak model lacks: how to read a Python
traceback properly, and which tools show what a program does when there
is no IDE debugger, only a terminal. It covers regressions, "works here,
fails there", bugs that vanish when watched, hangs, crashes with no
traceback, and memory growth. It ends where a domain ladder begins: a
failing test, a failing pod, missing telemetry.

## 2. The environment it is written for

- **A weak model** (MiniMax 2.7 for evals) in Zed's agent on Windows with
  PowerShell, air gapped, Python through uv, packages only from the
  internal mirror, no web: the answer is in the output, the code and the
  installed source.
- **No debugger UI.** No gutter breakpoints, no watch window, no
  stepping: only commands that run to the end and print. Anything that
  waits for the keyboard (`breakpoint()`, `pdb`, `input()`, `pytest
  --pdb`) is treated as a hang unless a script drives it. Whether Zed's
  terminal tool gives a command any stdin, and how long it waits before
  giving up, is *to verify in the lab*.
- **Windows changes the tools.** There is no `SIGUSR1`, so
  `faulthandler.register` cannot dump a live process on demand;
  `faulthandler.dump_traceback_later` is used instead. No `resource`
  module. `open()` without `encoding` uses the locale code page, not
  UTF-8: a common "passes on Linux CI, fails here" cause (Python 3.15 is
  due to change the default: *to verify in the lab*). Variables are set
  with `$env:NAME = "1"` and removed with `Remove-Item Env:NAME`.
- **Nothing extra installed.** The core uses only the standard library:
  `faulthandler`, `traceback`, `logging`, `pdb`, `tracemalloc`, asyncio
  debug mode. `py-spy` only if the environment already has it.

## 3. The kinds of task

| Kind | Asked to | Answer shape |
| --- | --- | --- |
| **Fix** | find and fix a bug from a report or a symptom | the cause, the reproduction, the fix, and the proof run twice: fails without, passes with |
| **Reproduce** | make a reported bug happen on demand | one command that fails every time, or at a stated rate over N runs |
| **Shrink** | cut a large failing case down | the smallest input, config and code that still fail, and what was removed |
| **Read** | explain a traceback | the exception that started it, the frame that matters, and the chain between them |
| **Inspect** | see a value or a path at runtime, with no IDE | the probe, its output, and confirmation it was removed |
| **Regression** | it worked at an older commit | the first bad commit (via git), and the cause in its diff |
| **Differ** | works here, fails there | the one difference that decides it, shown by flipping it |
| **Intermittent** | fails sometimes, or stops failing when watched | a way to make it fail every time, then the cause |
| **Hang** | hangs, freezes or deadlocks | every thread's stack at the hang, and the wait that never ends |
| **Crash** | the process dies with no Python traceback | the faulthandler dump and the frame it names |
| **Memory** | memory keeps growing | the allocation site that grows, from two snapshots |

Invariants `SKILL.md` will carry: no fix before a reproduction that
fails; one change between runs; a fix is proven only by the same
reproduction failing without it; never silence an exception to pass;
nothing that waits for the keyboard; every probe removed before the end.

## 4. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Fixing the symptom** | `KeyError` at `report.py:40` fixed with `.get(key, 0)` there, when the parser upstream dropped the key |
| **Guessing a cause** | "probably a race condition" or "probably an encoding issue", and an edit, before the bug was reproduced once |
| **Several changes at once** | changes the parser, the default and the retry in one go; it passes, and nobody knows which change mattered or what else broke |
| **Works on my machine** | the bug does not reproduce locally, so the model declares it fixed, or blames CI, instead of listing what differs |
| **Silencing the exception** | `try: ... except Exception: pass`, `contextlib.suppress`, a broad `except` that logs and returns `None` |
| **Fix not proven** | the reproduction passes after the fix, but it also passed before: it never reproduced the bug |
| **Last exception read** | in a chain, fixes the final exception, raised while handling the first; or blames the library frame that raised instead of the project frame that passed the bad value |
| **Debugger left waiting** | runs code with `breakpoint()` in it, or `pytest --pdb`; the terminal hangs until the tool gives up |
| **Probes left behind** | `print`, `breakpoint()`, a `DEBUG` log level or a `sleep` still in the diff |
| **Timing fixed with time** | a `sleep`, a longer timeout or a retry added to a race until it stops showing |
| **Hang killed and retried** | the process is stopped and run again, with no stack dump taken |
| **Regression by reading** | reads a 40-commit diff and guesses, when a bisect with the reproduction would name the commit |
| **Memory fixed with `gc.collect()`** | adds collections or restarts instead of finding what holds the references |

## 5. Layout

```
skills/debugging/
  SKILL.md           router over the eleven kinds, invariants, headings
  glossary.md        reproduction, minimal case, probe, frame that matters
  core/
    loop.md          the fixed loop; its hypothesis step is seniority's
    reproduce.md     from a report to one failing command, as a script
    shrink.md        halve input, config and code until nothing can go
    prove-the-fix.md passes with the fix, fails with it reverted
    read-traceback.md  which exception started it, which frame matters
    inspect.md       choose a probe, place it at a boundary, remove it
    regression.md    is it one; a good commit; the bisect script; git
    differ.md        list every difference, then flip one at a time
    intermittent.md  count the failure rate, force the timing
    hang.md          dump every thread, read the wait that never ends
    crash.md         no traceback: faulthandler, native code, exit codes
    memory.md        tracemalloc snapshots, what holds the reference
    handoff.md       where pytest, deployment, observability take over
  python/
    tracebacks.md    real shapes: chained, `from None`, notes, groups
    async.md         task tracebacks, `TaskGroup`, a blocked event loop
    versions.md      what a debugger sees change from 3.11 to 3.14
  tools/
    probes.md        marked stderr prints, `traceback.print_stack`
    pdb.md           no keyboard: `-c`, piped stdin, `PYTHONBREAKPOINT=0`
    faulthandler.md  `-X faulthandler`, `dump_traceback_later`, Windows
    logging.md       temporary debug logging for one logger
    tracemalloc.md   `-X tracemalloc`, snapshots, `compare_to`
    py-spy.md        `dump` and `top`, only if installed
    powershell.md    env vars, stderr capture, run N times, time limits
  recipes/
    repro_template.py  exits 0 or 1; usable by `git bisect run`
    run_n.ps1        run N times, count failures, keep the first log
    watchdog.py      run a script, dump all stacks after N seconds
    mem_diff.py      two tracemalloc snapshots, the top growing lines
  examples/          symptom-vs-cause, works-here-fails-there, deadlock
  evals/             evals.json and one sandbox per failure
```

## 6. Dependencies and boundaries

From the roadmap: debugging **needs** nothing, **relies by name** on
offline-docs, and **touches** pytest, navigation, observability and
deployment. It owns the generic loop; the others keep their ladders.

- **seniority** (always loaded) owns the habits: `hypothesis-loop.md`
  (two causes, a test that could disprove each, one change at a time),
  `reading-errors.md` (first error, categories) and `loop-breaker.md`.
  Debugging calls the hypothesis loop by name and does not restate it.
  It adds what surrounds that step (a runnable reproduction, shrinking,
  proof by reverting) and the Python and tool facts seniority lacks.
  `tracebacks.md` refines one seniority rule: the deepest project frame
  is where to start reading, not always where the cause is.
- **pytest** owns reading a test failure (`read-failure.md`), test or
  code (`test-or-code.md`), flaky tests from order, seeds, shared state
  and xdist (`flaky-and-slow.md`), and writing the regression test. A
  failing test enters pytest first; when the code is wrong and the cause
  is not in the output, pytest hands over to the loop, and the loop hands
  back to pytest's `write-test.md` for the regression test. A race in the
  code under test, not in test order, is debugging's.
- **deployment** owns the thirteen-hop ladder in `core/debug.md`. When it
  stops at "the container crashes with a Python traceback", debugging
  takes the traceback; a cause in deployed config goes back to deployment.
- **observability** owns instrumentation, querying the backend, and the
  ladder for missing telemetry. Debugging uses logging only as a
  temporary probe. A production trace is evidence for a reproduction;
  finding it in the backend is observability's.
- **navigation** owns finding code and the Environment question (which
  interpreter and packages run). `differ.md` uses its probes instead of
  its own. Reading history (`git log -S`, blame) is navigation's.
- **offline-docs** (by name): when the raising frame is in a library,
  what the library expects comes from its installed source and `help()`.
- **git** (proposed, by name) owns bisect mechanics. Debugging owns
  deciding it is a regression, finding a good commit, and the script
  `bisect run` calls.
- **packaging** (proposed, by name): why two machines resolved different
  versions of a package is packaging's; debugging only shows the skew.

### Proposed changes to the roadmap

1. Add **git** and **packaging** to debugging's "Relies on by name".
   The boundary table gives bisect to git, but the dependency table
   leaves it out; `differ.md` points at packaging for version skew.
2. Add a boundary row for **seniority**: "hypothesis loop, first error,
   loop breaking: seniority; reproduction, shrinking, proof of the fix,
   traceback and tool facts: debugging". It is the likeliest duplicate.
3. Split the pytest side of "the generic debugging loop": pytest owns
   **flaky tests** (order, seeds, xdist); debugging owns timing bugs in
   the code under test.

## 7. How it will be verified

Versions, to agree with the other plans (roadmap R2): **Python 3.12**
as main, as pytest pinned, with 3.13 and 3.14 where a debugger sees a
difference (3.13's coloured tracebacks and pdb changes, 3.14's
`python -m pdb -p` attach and `python -m asyncio ps`: *to verify in the
lab*); **pytest 9.1.1**; **git** as the git plan pins; **uv** and
**py-spy** as the mirror holds them.

The lab must:

1. Capture every traceback shape in `python/` from a real run on each
   pinned Python, pasted as it came, never retyped.
2. Run every pdb sequence in `tools/pdb.md` through Zed's terminal tool
   on Windows (`-c`, piped stdin, a `breakpoint()` reached, the same with
   `PYTHONBREAKPOINT=0`) and record which ones hang.
3. On Windows, deadlock two threads, block an asyncio loop, and crash
   native code (`ctypes.string_at(0)`); record each `watchdog.py` or
   `-X faulthandler` dump and the exit code.
4. Check `mem_diff.py` names the cache in a sandbox that leaks one, and
   `repro_template.py` under `git bisect run` names a planted commit.
5. Reproduce every eval bait; check every intended fix passes, and fails
   again when reverted. Then run the evals with the weak model.

What the lab cannot run on Windows is marked *not run* where stated.

## 8. Evals, written first

Each sandbox is a small Python project with a task, baiting one failure.

| Sandbox | Task | Bait | Pass |
| --- | --- | --- | --- |
| `missing-key` | fix a `KeyError` in a report | `.get()` at the raise site | fix in the parser that drops the key; reproduction added |
| `wrong-totals` | "totals are wrong sometimes", no traceback | edit before reproducing | a failing command first, then one hypothesis |
| `two-suspects` | two code smells, one is the bug | change both | one change, the other ruled out by a test |
| `utf8-ci` | passes in the Linux CI log, fails on Windows | "cannot reproduce" | names `open()` without `encoding`, shown by flipping `PYTHONUTF8` |
| `worker-crash` | a background worker dies | `except Exception: pass` | cause fixed, the exception still surfaces |
| `chained` | traceback with `During handling` | fix the last exception | fix the first; explain the chain |
| `from-none` | `ConfigError` raised `from None` | guess at config | print `__context__`, find the real error |
| `leftover-breakpoint` | run a script that has `breakpoint()` in it | terminal hangs | notices it, runs with `PYTHONBREAKPOINT=0`, removes it |
| `not-proven` | a fix and a test that passes either way | reports fixed | shows the test fails with the fix reverted, or says it cannot |
| `race` | a counter off by a few under threads | adds a `sleep` | makes it fail every time, fixes with a lock, counts N runs |
| `deadlock` | a script that hangs | kill and rerun | dump of both threads, names the lock order |
| `regression` | a test broke somewhere in 30 commits | reads diffs | bisect with a script, names the commit |
| `growing-cache` | memory grows per request | `gc.collect()` | tracemalloc diff names the cache |
| `task-group` | an `ExceptionGroup` with two errors | reads only one | both sub-exceptions reported and fixed |

## 9. Decisions needed

### DB1. The hypothesis step: seniority's or its own

*Recommended:* seniority's `hypothesis-loop.md`, by name, with a
two-line summary in `core/loop.md` so the loop reads alone. A copy would
drift.

### DB2. How much pdb to teach

An agent cannot type into a debugger. *Recommended:* scripted pdb only
(`-c`, piped input, post-mortem), and only if the lab shows it does not
hang in Zed; otherwise pdb is "do not use", and probes, `faulthandler`
and `traceback` do the work.

### DB3. py-spy

Is it in the mirror, and does it need administrator rights on Windows
(*to verify*)? *Recommended:* optional; every procedure has a standard
library path first.

### DB4. The regression test after a fix

*Recommended:* with a test suite, the reproduction becomes a test through
pytest's `write-test.md`, noted under seniority's *Decided for you*.
Without one, the reproduction script is reported, not added.

### DB5. Answer headings

*Recommended:* `## Cause`, `## Reproduction`, `## Fix`, `## Proof` (the
run with the fix and the run without), `none` when empty, before
pytest's and seniority's headings.

### DB6. A Windows lab

*Recommended:* a Windows machine for lab steps 2 and 3 (signals,
encodings, PowerShell piping, Zed's terminal); the rest in the Linux
build container, as for the other skills.

### DB7. Slowness

*Recommended:* out of scope unless it is a hang; profiling can be a
later file, and production latency is observability's.
