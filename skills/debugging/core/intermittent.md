# Intermittent

**Verdict you produce:** the failure rate before, a way to make it fail
every time, the cause, and the rate after the fix.

```
rate before:  <k of N, with the command>
forced:       <what made it fail every time, without changing the code under test> -> <N of N>
cause:        <the shared state or timing, file:line>
fix:          <lock, queue, ordering, passing the value in; never a sleep or a retry>
rate after:   <0 of N with the fix; N of N again with it reverted>
```

A bug that fails sometimes has a cause that is there every time; only
the timing or the input changes. Count it, then take the chance away.

## Whose is it

| Fails sometimes because of | Owner |
| --- | --- |
| test order, random seeds, pytest-xdist workers, state shared between tests | pytest's `core/flaky-and-slow.md` |
| threads, processes or asyncio tasks in the code under test, time of day, input that varies | this file |

## Steps

1. **Count it.** Run the reproduction N times (10, or 20 for rare ones)
   and write the rate: "0 of 10" is a finding too.

   ```powershell
   .\run_n.ps1 -Times 20 -TimeoutSeconds 60 -- uv run python ..\repro_race.py
   ```

   (`recipes/run_n.ps1`; each run gets an empty stdin and a time limit.)
2. **List what varies between runs**: thread scheduling, task order, the
   clock, random values, input order, a service's answers. Each one is a
   hypothesis (seniority's `core/hypothesis-loop.md`).
3. **Take the chance away, one hypothesis at a time**, in the
   reproduction, not in the code under test:

   | Varies | Force it |
   | --- | --- |
   | thread switches | `sys.setswitchinterval(1e-6)` at the top of the repro script (`python/threads.md`) |
   | how often the racy code runs | more threads, more iterations |
   | the clock | pass the time in, or patch it where it is used (pytest's `core/mocking.md`) |
   | random values | seed them, or loop over the values that fail |

   *lab (race sandbox, 3.12.14, 8 threads x 10 000 calls):* 0 of 40 runs
   failed with the default switch interval of 0.005 s; with
   `sys.setswitchinterval(1e-6)` 10 of 10 failed, one counting 59 792 of
   160 000. Forced, 5 of 5 failed on 3.13.15 and on 3.14.7 too.
4. **Name the cause** from what the forcing showed: usually a read, a
   Python-level call, then a write of the same shared value. In the lab
   `current = self.hits.get(path, 0)`, then `weight(path)`, then the
   write: another thread ran in between.
5. **Fix it** so the timing cannot matter: a `threading.Lock` around the
   read and the write, a queue with one owner, an atomic operation, or
   passing the value in.
6. **Prove it with rates** (`core/prove-the-fix.md`): the forced
   reproduction gives 0 of N with the fix and fails again without it.
   *lab:* 10 of 10 failed without the lock, 0 of 10 with it.

## Probes change timing

A print, a log line or a debugger stop inside racy code changes when
threads switch. *lab:* one `print(..., file=sys.stderr)` between the
read and the write turned a counter that never lost a hit into one that
lost three quarters of them (4 066 of 16 000). The reverse also happens:
a probe can make a race disappear. Count results instead: collect values
in a list and print them after the threads end.

## Never

- Never add a `sleep`, a longer timeout or a retry to make a race stop
  showing. It changes the rate, not the cause.
- Never call a rate from fewer runs than it took to see the failure.
- Never "fix" by making the code single-threaded unasked; that is a
  design change.
- Never say "flaky" without the rate and what varies.
