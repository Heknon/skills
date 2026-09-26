# Recipes

Complete files that ran in the lab. Copy one next to the project (the
parent folder keeps it out of the project and out of git), change only
what its top comment says, and run it from the project root so the
project imports as it normally does. Each one puts the current folder
on `sys.path` for that reason. None needs a package beyond the standard
library.

| File | Does | Run in the lab |
| --- | --- | --- |
| `repro_template.py` | a reproduction that answers with its exit code: 0 good, 1 the bug, 125 cannot test; usable by `git bisect run` | named "Tidy conversion helpers" in the regression sandbox, skipping the commit that did not import (3.12.14, git 2.43.0) |
| `watchdog.py` | runs a script or `-m module`; after N seconds prints every thread's stack and exits 1 | dumped the deadlock sandbox on 3.12.14, 3.13.15 and 3.14.7; a run that ended in time kept its own exit code and printed nothing extra |
| `locals_on_error.py` | runs a script or `-m module`; on an exception prints the traceback, then each project frame's locals, for every exception in a chain or group | showed `'﻿region'` (missing-key), both sub-exceptions (task-group), the error hidden by `from None` (from-none); 3.12 to 3.14 |
| `mem_diff.py` | calls a function, snapshots, calls it N more times, snapshots, prints the lines that grew | named `render.py` lines 16 and 19 in the growing-cache sandbox, and `+0.0 KiB` after the fix |
| `run_n.ps1` | runs a command N times, each with an empty stdin and a time limit, counts failures, keeps the first failure's output in the temporary folder | PowerShell 7.4.6 on Linux: counted the race sandbox, stopped the deadlock sandbox at the limit with no process left, ended a `(Pdb)` prompt at once; not run on Windows |

## Typical commands

```powershell
uv run python ..\repro_bug.py; $LASTEXITCODE
uv run python ..\watchdog.py 10 -m sync
uv run python ..\locals_on_error.py -m sales data\may.csv
uv run python ..\mem_diff.py profiles.serve:serve 1000 --frames 4
..\run_n.ps1 -Times 20 -TimeoutSeconds 60 -- uv run python ..\repro_bug.py
```

`repro_template.py` must be copied, because you change it. The others
can also run from the skill's folder by their full path (*lab:* all
four did), since they take everything from the command line.
