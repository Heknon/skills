# Hang

**Verdict you produce:** every thread's stack at the hang, and the wait
that never ends.

```
command:  <how it was run, with the time limit and the dump>
dump:     <for each thread: its name or id, and the project frame it waits in, copied>
waits on: <the lock, queue, join, socket, subprocess or event each thread waits for>
cause:    <why that wait never ends: "shipper holds inventory_lock and waits for ledger_lock; auditor holds ledger_lock and waits for inventory_lock">
```

A hung process shows nothing. Stopping it and running it again shows
nothing either: the evidence is where each thread was at the moment it
stopped moving. Take that dump first, before any hypothesis.

## Steps

1. **Never let the terminal tool's time limit end the run.** When a
   command might hang, run it under a time limit that dumps the stacks:

   ```powershell
   uv run python ..\watchdog.py 10 -m sync
   ```

   `recipes/watchdog.py` uses `faulthandler.dump_traceback_later`, which
   works on Windows and Linux. It prints `Timeout (0:00:10)!` and every
   thread's stack, then exits with code 1.
2. **If the process is already running** and was not started that way:

   | Have | Command | Notes |
   | --- | --- | --- |
   | Python 3.14 | `uv run python -m pdb -p <pid>` with the commands piped in | `tools/pdb.md`; *lab:* `w` and `p total, i` printed, then end of input detached and the target kept running |
   | Python 3.14, asyncio | `uv run python -m asyncio pstree <pid>` or `ps <pid>` | `python/async.md` |
   | py-spy installed | `py-spy dump --pid <pid>` | `tools/py-spy.md` |
   | Linux, started with `-X faulthandler` | `kill -ABRT <pid>` | *lab:* dumped all threads; plain `timeout` (SIGTERM) dumped nothing |
   | none of these | stop it and start it again under `watchdog.py` | |

3. **Read each thread's stack from its top project frame**, the last
   line in the project's files, and copy the source line. What is it
   waiting for?

   | Top project line | Waits for |
   | --- | --- |
   | `with some_lock:` or `lock.acquire()` | another thread to release that lock |
   | `thread.join()`, `future.result()` | that thread or task to end |
   | `queue.get()` | something to be put on the queue |
   | `selectors.py ... in select` under `asyncio/base_events.py` | the event loop is idle: every task waits; dump the tasks (`python/async.md`) |
   | a socket or HTTP call | the other side; air gapped, maybe a host it cannot reach |
   | `input()` or a `(Pdb)` prompt | the keyboard (`tools/pdb.md`) |
   | the same few lines in each of several dumps | a busy loop: nothing waits, the loop never ends |

4. **For locks, pair the threads.** For each thread write what it holds
   (the `with` blocks it is inside) and what it waits for (the line it
   is on). A cycle is a deadlock. *lab (deadlock sandbox):*

   ```
   Timeout (0:00:03)!
   Thread 0x00007ff7889fd6c0 (most recent call first):
     File "/home/user/dbg/sb/deadlock/sync/store.py", line 27 in reconcile
     File "/home/user/dbg/sb/deadlock/sync/__main__.py", line 13 in auditor
     ...
   Thread 0x00007ff7891fe6c0 (most recent call first):
     File "/home/user/dbg/sb/deadlock/sync/store.py", line 19 in ship
     File "/home/user/dbg/sb/deadlock/sync/__main__.py", line 8 in shipper
     ...
   ```

   (`...` marks the `threading.py` frames cut from this copy.) Line 19
   is `with ledger_lock:` inside `with inventory_lock:`; line 27
   is `with inventory_lock:` inside `with ledger_lock:`. Each holds the
   lock the other waits for.
5. **For a busy loop, dump more than once** and compare:
   `faulthandler.dump_traceback_later(1, repeat=True)` as a probe.
   *lab:* three dumps a second apart showed `settle` at lines 9, 8, 9:
   the `while` loop, never reaching its end condition.
6. **Fix the wait, not the symptom**: take locks in one order
   everywhere; give a queue its sentinel; await the task that never
   finishes; give an external call a timeout **and** handle it.
7. **Prove it** (`core/prove-the-fix.md`) with N runs under the time
   limit. *lab:* after taking the locks in one order, 10 of 10 runs
   printed `sync finished` under `watchdog.py 10`.

## Never

- Never kill a hung process and run it again without a dump.
- Never "fix" a deadlock with `acquire(timeout=...)`, a retry or a
  `sleep`: the cycle is still there.
- Never read the main thread only: in a deadlock the main thread usually
  waits in `join`, and the cause is in the other threads.
