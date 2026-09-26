# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| symptom | What was seen, copied exactly: the message, the wrong value, the hang, the exit code, and where. |
| cause | The line or value that, changed back, makes the symptom go away; usually upstream of where the symptom shows. |
| reproduction | One command that shows the symptom on demand, with a known result: fails every time, or at a counted rate over N runs. |
| repro script | A reproduction written as a script that exits 0 when the bug is absent, 1 when it is present and 125 when the version cannot be tested (`recipes/repro_template.py`). |
| failure rate | How many of N runs of the reproduction failed, written "7 of 20"; the only honest description of an intermittent bug. |
| minimal case | The smallest input, configuration and code that still fail the same way; nothing left in it can be removed without the failure going. |
| hypothesis | One possible cause, with a test that could disprove it; seniority's `core/hypothesis-loop.md` owns the form. |
| probe | Temporary code or a temporary setting that shows a value or a path at runtime: a marked print, a debug logger, a stack dump. It is removed before the end. |
| boundary | A place where data passes from one part to another: a function's arguments, a return value, a file read, a queue; the best place for a probe. |
| frame | One line of a traceback: a file, a line number and a function, plus the source line. |
| raising frame | The last frame of a traceback, where the exception was raised; often in a library. |
| deepest project frame | The last frame in the project's own files; where to start reading, not always where the cause is. |
| frame that matters | The frame whose code or input is wrong; found by reading from the deepest project frame back towards the caller. |
| chain | Two or more tracebacks printed together because one exception was raised while another was being handled (`__context__`) or from it (`__cause__`). |
| first exception | The top traceback in a chain: the one that started it. |
| exception group | An `ExceptionGroup` holding several unrelated exceptions, each with its own traceback, printed with `|` borders. |
| prove the fix | Run the same reproduction with the fix (passes) and with the fix reverted (fails). |
| regression | A bug that was not there at an older version; found by bisecting between a good and a bad commit. |
| good commit | A commit where the reproduction passes, checked by running it, not assumed. |
| stack dump | Every thread's current stack, printed by `faulthandler`, `py-spy dump` or 3.14's `python -m pdb -p`, while a process hangs or when it crashes. |
| hang | A process that makes no progress: every thread waits, or one loops. |
| deadlock | A hang where each thread waits for a lock another one holds. |
| crash | The process died without a Python traceback: a signal or a Windows exception code, or `os._exit`. |
| wait for the keyboard | A program stopped at a prompt (`(Pdb)`, `input()`, `[y/n]`); in a terminal tool, a hang until the tool's time limit. |
| switch interval | How often the interpreter may switch between threads (`sys.getswitchinterval()`, 0.005 s by default); shrinking it makes races show. |
| snapshot | A `tracemalloc` record of every live allocation and the line that made it; two are compared to find growth. |
