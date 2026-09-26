# The loop

**Verdict you produce:** the four answer headings, each filled from
something you ran.

```
cause:        <file:line and one sentence: what is wrong there, and why it gives the symptom>
reproduction: <one command, and its result before the fix: "exit 1, KeyError: 'region'" or "7 of 20 failed">
fix:          <the change, at the cause>
proof:        <the same command with the fix: passes; with the fix reverted: fails again>
```

Every bug goes through the same seven steps, in order. The kind of bug
changes how each step is done, not the order. Never skip ahead: an edit
before step 2 is a guess, and a fix without step 6 is a claim.

## Steps

1. **Is it this skill's?** A failing test starts in pytest's
   `core/read-failure.md`; a failing pipeline, job or pod in deployment's
   `core/debug.md`; missing or wrong telemetry in observability. Come back
   here when they hand over (`core/handoff.md`).
2. **Write the symptom exactly**, copied, not described: the first error
   (seniority's `core/reading-errors.md`), the wrong value next to the
   right one, the exit code, how long a hang lasted. For a traceback, read
   it whole now (`core/read-traceback.md`).
3. **Reproduce it** (`core/reproduce.md`): one command that shows the
   symptom, and its result. No edit to the code before this command has
   failed in front of you. If it will not fail, that is the first finding:
   go to `core/differ.md` or `core/intermittent.md`.
4. **Shrink it** if the case is large or slow (`core/shrink.md`): the
   smaller the case, the fewer the causes.
5. **Find the cause with seniority's hypothesis loop**
   (`core/hypothesis-loop.md`). In two lines: write at least two causes,
   each with a test that could disprove it; run one test at a time and
   change nothing else. The tests this skill adds:

   | To tell causes apart by | Use |
   | --- | --- |
   | a value at a boundary | a probe (`core/inspect.md`) |
   | what differs between two runs | one flip at a time (`core/differ.md`) |
   | which commit | a bisect with the repro script (`core/regression.md`) |
   | where threads wait | a stack dump (`core/hang.md`) |
   | what grows | two snapshots (`core/memory.md`) |
   | where the process died | `faulthandler` (`core/crash.md`) |

6. **Fix the cause, then prove it** (`core/prove-the-fix.md`): the same
   reproduction passes with the fix and fails with it reverted. Fix where
   the frame that matters is, which is often upstream of the frame that
   raised.
7. **Clean up.** Remove every probe (search for your marker), restore
   any file you reverted, and decide what happens to the reproduction:
   with a test suite, it becomes a test through pytest's
   `core/write-test.md`; without one, it is reported, not added (write
   the choice under seniority's *Decided for you*).

## The kinds, and where they enter the loop

| Symptom | Start with |
| --- | --- |
| a traceback | `core/read-traceback.md`, then step 3 |
| a wrong value, no error | `core/reproduce.md`: the reproduction checks the value |
| worked at an older version | `core/regression.md` |
| works here, fails there | `core/differ.md` |
| fails sometimes, or not when watched | `core/intermittent.md` |
| hangs, freezes | `core/hang.md` |
| dies with no traceback | `core/crash.md` |
| memory keeps growing | `core/memory.md` |

## Never

- Never edit code before a reproduction has failed in front of you.
- Never change two things between runs.
- Never fix the line that raised without asking why the value was wrong
  there (`core/read-traceback.md`).
- Never silence an exception to make the symptom go (`except: pass`,
  `contextlib.suppress`, a broad `except` that logs and returns `None`).
  A fix that catches an exception must still report it.
- Never add a `sleep`, a longer timeout or a retry as the fix for a race
  or a hang (`core/intermittent.md`).
- Never run anything that can wait for the keyboard (`tools/pdb.md`).
- Never leave a probe behind.

## Stop and ask

- The symptom cannot be reproduced and nothing that differs can be
  flipped here (the data, the machine or the service is out of reach):
  report the symptom, what was tried, and what would reproduce it.
- The fix changes behaviour someone may rely on (a default, what is
  raised or returned): show the reproduction and ask.
