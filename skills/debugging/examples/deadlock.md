# Worked example: a hang, read from a stack dump

Kinds: Hang, Fix. Outputs are from a lab run on Python 3.12.14 in a copy
of the `deadlock` sandbox, with `watchdog.py` and `run_n.ps1` copied to
the parent folder. The lab ran on Linux (`../watchdog.py`, and
`run_n.ps1` in PowerShell 7.4); the commands are shown as typed on
Windows, not run there.

## The ask

> `uv run python -m sync` hangs and never finishes. Find out why and fix
> it.

## Steps

1. **Do not run it plainly**: it would wait until the terminal tool
   gives up, and show nothing. Run it under a time limit that dumps
   every thread (`core/hang.md`):

   ```powershell
   uv run python ..\watchdog.py 10 -m sync
   ```

   ```
   Timeout (0:00:10)!
   Thread 0x00007f36725426c0 (most recent call first):
     File "/home/user/dbg/ex3/sync/store.py", line 27 in reconcile
     File "/home/user/dbg/ex3/sync/__main__.py", line 13 in auditor
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1012 in run
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1075 in _bootstrap_inner
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1032 in _bootstrap

   Thread 0x00007f3672d436c0 (most recent call first):
     File "/home/user/dbg/ex3/sync/store.py", line 19 in ship
     File "/home/user/dbg/ex3/sync/__main__.py", line 8 in shipper
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1012 in run
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1075 in _bootstrap_inner
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1032 in _bootstrap

   Thread 0x00007f3673a1b740 (most recent call first):
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1169 in _wait_for_tstate_lock
     File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1149 in join
     File "/home/user/dbg/ex3/sync/__main__.py", line 20 in <module>
     File "<frozen runpy>", line 88 in _run_code
     File "<frozen runpy>", line 98 in _run_module_code
     File "<frozen runpy>", line 226 in run_module
     File "/home/user/dbg/ex3/../watchdog.py", line 36 in main
     File "/home/user/dbg/ex3/../watchdog.py", line 45 in <module>
   ```

   Exit 1, after 10 s. This dump is the reproduction's result.
2. **Read each thread's top project line** (`core/hang.md` step 3). The
   main thread waits in `join`: it waits for the others. In
   `sync/store.py`:

   ```
   16      with inventory_lock:            # ship
   19          with ledger_lock:            # shipper waits here
   24      with ledger_lock:               # reconcile
   27          with inventory_lock:         # auditor waits here
   ```

3. **Pair them**: the shipper holds `inventory_lock` (line 16) and waits
   for `ledger_lock` (line 19); the auditor holds `ledger_lock` (line
   24) and waits for `inventory_lock` (line 27). Each holds what the
   other waits for: a deadlock from taking the same two locks in
   opposite orders. The `write_slowly()` between the two `with` lines
   makes the overlap certain: it hung every run.
4. **Fix the order**, one order everywhere: `inventory_lock`, then
   `ledger_lock`.

   ```
    def reconcile():
   -    with ledger_lock:
   -        shipped = sum(q for kind, _, q in ledger if kind == "ship")
   -        write_slowly()
   -        with inventory_lock:
   +    with inventory_lock:
   +        with ledger_lock:
   +            shipped = sum(q for kind, _, q in ledger if kind == "ship")
   +            write_slowly()
                return shipped, sum(inventory.values())
   ```

5. **Prove it with N runs under the time limit**
   (`core/prove-the-fix.md`):

   ```powershell
   ..\run_n.ps1 -Times 10 -TimeoutSeconds 30 -- uv run python ..\watchdog.py 10 -m sync
   ```

   ```
   run 9: exit 0
   run 10: exit 0
   0 of 10 failed
   ```

   With the fix stashed (`git stash push -- sync/store.py`), the same
   command with `-Times 3` and a 5 s watchdog:

   ```
   3 of 3 failed
   ```

   and the kept output began `Timeout (0:00:05)!` with the auditor at
   `store.py", line 27 in reconcile`. Restored with `git stash pop`.

## The answer

```
## Cause
sync/store.py takes the same two locks in opposite orders: ship() holds
inventory_lock and then takes ledger_lock (line 19); reconcile() holds
ledger_lock and then takes inventory_lock (line 27). Run together, each
thread holds the lock the other waits for.

## Reproduction
uv run python ..\watchdog.py 10 -m sync -> after 10 s, "Timeout
(0:00:10)!", auditor at store.py:27, shipper at store.py:19, main thread
in join; exit 1. It hung every run.

## Fix
reconcile() now takes inventory_lock, then ledger_lock, the same order
as ship().

## Proof
With the fix: 10 runs under the watchdog, 0 of 10 failed, each printing
"sync finished". With the fix stashed: 3 of 3 timed out with the same
dump. Restored.

## Done when
uv run python -m sync finishes: observed in 10 of 10 runs.

## Not done
none

## Unverified
none

## Decided for you
Chose the lock order inventory_lock, then ledger_lock, the order ship()
already used, so only reconcile() changed.
```
