# Threads

**What it decides:** why a thread's failure did not stop the program,
how to make it visible, and what a race and a deadlock look like.
Checked on 3.12.14 and 3.14.7 unless marked.

## A thread that dies does not fail the program

An exception that ends a `threading.Thread` is printed to stderr by
`threading.excepthook`, and the rest of the program carries on. The exit
code stays 0. *lab (3.12.14):*

```
Exception in thread worker:
Traceback (most recent call last):
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1075, in _bootstrap_inner
    self.run()
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/threading.py", line 1012, in run
    self._target(*self._args, **self._kwargs)
  File "/home/user/dbg/worker/t.py", line 6, in worker
    print("done", 100 // job)
                  ~~~~^^~~~~
ZeroDivisionError: integer division or modulo by zero
done 20
main finished
```

Exit code 0. The first line names the thread (`name=` when it was
created). Read the traceback as usual; the two `threading.py` frames are
the thread's machinery. The same shape appeared in the worker-crash
sandbox as `imported 12 of 31 lines`, exit 0.

A `concurrent.futures` task is quieter still: its exception is stored in
the future and printed **only** when `future.result()` is called.
*lab:* three jobs, one dividing by zero, no `result()` call: output
`main finished`, exit 0, no traceback at all.

## Make the failure reach the main thread

| Code uses | Surface it with | Seen in the lab |
| --- | --- | --- |
| `concurrent.futures` | call `future.result()` for every future | the worker's `ZeroDivisionError` raised in the main thread, exit 1 |
| `threading.Thread` | a `threading.excepthook` that records the failure and calls `threading.__excepthook__(args)`, then a check after `join()` | `thread failed: ['worker']`, exit 1 |
| a worker you own | the worker catches, records the error and the item it was on, and the main thread reports them and exits non-zero | |

The fix of the cause comes first; surfacing is so the next failure is
not silent. A worker that catches and carries on must still report what
it skipped.

## What a race needs

A lost update needs a thread switch between reading a shared value and
writing it back. *lab:* with `current = self.hits; self.hits = current
+ n` (no call in between), 8 threads lost nothing in 10 runs, even with
`sys.setswitchinterval(1e-6)`. With a Python function call between the
read and the write (`current + weight(path)`), 10 of 10 forced runs lost
hits. Look for a read, a call, then a write of the same shared value.

- `sys.getswitchinterval()` is `0.005` by default (*lab*, 3.12 and
  3.14). `sys.setswitchinterval(1e-6)` in the reproduction makes
  switches as frequent as possible (`core/intermittent.md`).
- The fix is a `threading.Lock` held around the read and the write
  together (*lab:* 0 of 10 lost).
- Free-threaded builds (`3.14t`) were not tested.

## What a deadlock looks like in a dump

Each thread is inside a `with` for one lock and on a line that takes
another. `core/hang.md` has the lab dump. The main thread waits in
`join`:

| Version | Main thread's top frame in the dump (*lab*) |
| --- | --- |
| 3.12.14 | `threading.py", line 1169 in _wait_for_tstate_lock` then `join` |
| 3.13.15 | `threading.py", line 1095 in join` |
| 3.14.7 | `threading.py", line 1133 in join`, and each thread's name in brackets: `Thread 0x... [audit]` |

## Never

- Never read "exit 0" as "every thread finished its work".
- Never fix a race with `time.sleep` or by lowering the number of
  threads.
