# py-spy

**What it decides:** where every thread of a running Python process is,
from outside, without changing or restarting it. Optional: use it only
if it is already installed; every procedure has a standard library path
first. Checked with py-spy 0.4.2 from the public index, on Linux.

## Is it there

```powershell
uv run py-spy --version
```

If the command is not found, do not install it (air gapped: it must come
from the mirror, and adding it changes the project); use
`recipes/watchdog.py` or, on 3.14, `python -m pdb -p`. Whether py-spy
needs administrator rights on Windows was not checked (not run on
Windows).

## Dump the stacks

```powershell
uv run py-spy dump --pid <pid>
```

*lab (deadlock, Python 3.12.3):*

```
Process 20433: /usr/bin/python3.12 deadlock.py
Python v3.12.3 (/usr/bin/python3.12)

Thread 20433 (idle): "MainThread"
    _wait_for_tstate_lock (threading.py:1167)
    join (threading.py:1147)
    <module> (deadlock.py:26)
Thread 20435 (idle): "transfer"
    transfer (deadlock.py:11)
    run (threading.py:1010)
    _bootstrap_inner (threading.py:1073)
    _bootstrap (threading.py:1030)
Thread 20436 (idle): "audit"
    audit (deadlock.py:18)
    ...
```

Most recent call first, like `faulthandler`, with thread names on 3.12
and 3.13 (on 3.14.7 the names were missing, *lab*).

| Option | *lab* result |
| --- | --- |
| `--locals` (`-l`) | the arguments and locals of each frame: `n: 600`, `total: 210`, `i: 20` |
| `--native` (`-n`) | also C frames of extensions; listed in `--help`, not run |
| `record --pid <pid> --duration 2 --format raw -o rec.txt` | samples for 2 s and writes one line per stack with a count |
| `top --pid <pid>` | **does not work in a terminal tool**: `Error: Not a tty (os error 25)`, exit 1 |

Run as root in the lab. One `dump` started one second after the target
failed with `Error: Failed to find python version from target process`;
two seconds after, it worked. Wait until the program is running, and try
again once before giving up.

## Never

- Never install py-spy to debug; use the standard library path.
- Never use `py-spy top` from an agent.
