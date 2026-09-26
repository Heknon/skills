# asyncio

**What it decides:** what asyncio's own messages mean, how to see where
every task waits, and how to find a call that blocks the loop.
*lab* outputs are from 3.12.14 unless marked; 3.14.7 printed the same
messages.

## Messages and what they mean

| Seen | Means | Next |
| --- | --- | --- |
| `ExceptionGroup: unhandled errors in a TaskGroup (2 sub-exceptions)` | two tasks in a `TaskGroup` failed; the others were cancelled | read and fix every numbered sub-exception (`python/tracebacks.md`) |
| `Task exception was never retrieved` then `future: <Task finished name='Task-2' coro=<refresh() done, defined at ...never.py:4> exception=ConnectionError('prices: refused')>` | a task started with `create_task` failed and nothing awaited it; printed when the task is destroyed; exit code unchanged (*lab:* exit 0) | keep a reference and await it, or use a `TaskGroup` |
| `RuntimeWarning: coroutine 'save' was never awaited` at `noawait.py:10` | a coroutine function was called without `await`: its body never ran | add the `await` at the named line |
| `Executing <Task finished name='Task-1' coro=<main() done, ...> ...> took 0.300 seconds` | debug mode only: one step of a task ran 0.3 s without yielding: something blocked the loop | find the blocking call in that task (below) |

## Debug mode

`$env:PYTHONASYNCIODEBUG = "1"` or `uv run python -X dev ...` turns it
on (*lab:* both printed the slow-step line; `-X dev` also enables
`faulthandler`). What it adds, seen in the lab:

- the slow-step line above, for any step over 0.1 s (the
  `loop.slow_callback_duration` default);
- for "never retrieved", a `source_traceback: Object created at` block
  that shows the `create_task` line;
- for "never awaited", a `Coroutine created at` block ending at the call
  without `await`.

The slow-step line names the **task**, not the line that blocked. To
find the line, dump the task's stack while it blocks, or run
`faulthandler.dump_traceback_later` (`tools/faulthandler.md`): a
blocking call shows as the main thread sitting in it, for example
`time.sleep`, a synchronous HTTP call or a file read. *lab:* a dump
after 0.1 s had `File "blocked.py", line 6 in handler` on top, the
`time.sleep(0.3)` line, above the asyncio frames.

## Where every task waits

A `faulthandler` dump of a hung asyncio program shows only the loop
waiting, not the tasks. *lab (3.12.14):*

```
Timeout (0:00:01)!
Thread 0x00007f1a27ac4740 (most recent call first):
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/selectors.py", line 468 in select
  File "/root/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu/lib/python3.12/asyncio/base_events.py", line 1961 in _run_once
  ...
```

That means: the loop is idle, every task is waiting for something. Get
the tasks' stacks:

**Python 3.14, from outside** (*lab*, 3.14.7 on Linux; not run on
Windows):

```powershell
uv run python -m asyncio pstree <pid>
uv run python -m asyncio ps <pid>
```

```
└── (T) Task-1
    └──  main /home/user/dbg/aio/stuck.py:12
        └──  TaskGroup.__aexit__ /root/.local/share/uv/python/cpython-3.14.7-linux-x86_64-gnu/lib/python3.14/asyncio/taskgroups.py:72
            └──  TaskGroup._aexit /root/.local/share/uv/python/cpython-3.14.7-linux-x86_64-gnu/lib/python3.14/asyncio/taskgroups.py:121
                ├── (T) consumer
                │   └──  consumer /home/user/dbg/aio/stuck.py:6
                │       └──  Queue.get /root/.local/share/uv/python/cpython-3.14.7-linux-x86_64-gnu/lib/python3.14/asyncio/queues.py:186
                └── (T) ticker
                    └──  sleep /root/.local/share/uv/python/cpython-3.14.7-linux-x86_64-gnu/lib/python3.14/asyncio/tasks.py:705
```

`consumer` waits on `Queue.get` at `stuck.py:6`: nothing puts to the
queue. `ps` prints the same as a table, one task per row.

**Python 3.12 and 3.13, a probe** (marked, removed afterwards):

```python
def dump_tasks():  # DBG
    for task in asyncio.all_tasks():
        print(f"--- task {task.get_name()}", file=sys.stderr)
        task.print_stack(file=sys.stderr)

# first line inside the main coroutine:
asyncio.get_running_loop().call_later(2, dump_tasks)  # DBG
```

*lab:* after 2 s it printed each task, for example:

```
--- task consumer
Stack for <Task pending name='consumer' coro=<consumer() running at /home/user/dbg/aio/taskdump.py:13> wait_for=<Future pending cb=[Task.task_wakeup()]> cb=[TaskGroup._on_task_done()]> (most recent call last):
  File "/home/user/dbg/aio/taskdump.py", line 13, in consumer
    item = await queue.get()
```

It only runs if the loop is free: if one call blocks the loop, the probe
never fires, and the `faulthandler` dump shows the blocking call instead.
Run it under a time limit (`recipes/watchdog.py`).

## Never

- Never drop the result of `asyncio.create_task(...)`; an unawaited
  task's error surfaces late or not at all.
- Never wrap a `TaskGroup` in `except*` or `try/except` to make an
  error go away; fix each sub-exception.
- Never call blocking functions (`time.sleep`, synchronous HTTP, heavy
  CPU work) inside a coroutine; debug mode's slow-step line shows them.
