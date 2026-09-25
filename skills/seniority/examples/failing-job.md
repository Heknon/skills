# Worked example: a failing job, a loop caught, a cause confirmed

Follow this when something fails and you must find out why and fix it.
Copy the order of the moments and the shape of the ledger lines. Change
the facts, not the shape.

## The ask

> The nightly export job has failed since Monday. Fix it.

## Start

**Scope** (`core/scope.md`). The ask is a change. The person will accept
it when the job's own command succeeds on a day that failed. Near the task
but not asked: a pandas deprecation warning seen in the logs. Budget: find
the cause of a failure, 25 steps.

```
goal: "The nightly export job has failed since Monday. Fix it."
done when: the cron line's command, run by hand with `--date 2026-09-21`, exits 0 and writes `out/2026-09-21.csv`
budget: 25 steps
scope out: the pandas FutureWarning in the job log
```

**Assumptions** (`core/assumptions.md`). Two from the list of silent
assumptions, and one from the person's words:

- the job runs with the project's `.venv` interpreter: if false, all work on
  the package set is wasted, and one call checks it. Check first.
- the failure reproduces locally: if false, the fix cannot be observed.
- "since Monday" means something changed on Monday: cheap to check in the
  history.

**First step** (`core/first-step.md`). The fact that changes the most is
whether it fails here. Reproduce first.

## Investigate

Step 1 reproduces it. **Reading the error** (`core/reading-errors.md`): the
first error is `ModuleNotFoundError: No module named 'yaml'`, category *not
installed*, whose first check is which interpreter runs.

Step 2 shows `pyyaml` is installed in `.venv`. The model then tries the
install again (step 3), which returns the same as a check it already had.
Step 4 runs the job again: same failure as step 1. Steps 3 and 4 give no
new fact. **Loop rule 2 fires.** Step 4 also repeats step 1 with the same
result, which the ledger checker reports as a warning: a third run would
break loop rule 1.

**Stuck** (`core/loop-breaker.md`). Reread the goal. The approach so far is
"make sure the package is installed". Change the approach, not the
parameters: stop looking at the package, look at which interpreter the job
uses. The `stuck:` line records it.

**Hypothesis loop** (`core/hypothesis-loop.md`). Two causes, each with a
test that could fail. H1 is the person's implied one: something changed
in the dependencies on Monday. H2 comes from the error category: the job
runs a different interpreter.

Step 5 prints the interpreter from inside the job's command: the system
Python. Step 6 checks the history of the cron file: changed on Monday, from
`.venv/bin/python` to `python`. H2 confirmed; H1 ruled out by step 7,
which shows no dependency change since last week.

**Challenge the conclusion** (`core/challenge.md`, question 6): what else
would produce exactly these observations? A `PATH` change on the host
would too. But step 6 shows the cron line itself changed, and step 5 shows
the interpreter directly. The two observations together leave no other
cause.

## Fix and finish

Step 8 changes the cron line back. Step 9 runs the job exactly as `done
when` says: the fixed cron line's command, exit 0, file written. **Done** (`core/done.md`): observed at
step 9; the check ran the changed command; the diff is one line; no test
was touched.

## The ledger

```markdown
# Ledger

goal: "The nightly export job has failed since Monday. Fix it."
done when: the cron line's command, run by hand with `--date 2026-09-21`, exits 0 and writes `out/2026-09-21.csv`
budget: 25 steps
scope out: the pandas FutureWarning in the job log

## Assumptions

- A1 [false at step 5] the job runs with the project's .venv interpreter
- A2 [verified at step 1] the failure reproduces locally
- A3 [verified at step 6] something changed on Monday

## Hypotheses

- H1 [ruled out at step 7] a dependency changed on Monday | test: history of requirements.txt since last week | disproved if: no change since before Monday
- H2 [confirmed at step 6] the job runs a different interpreter than .venv | test: print sys.executable from the job's command, and the history of deploy/crontab | disproved if: it prints .venv/bin/python

## Steps

1. action: `python -m export.nightly --date 2026-09-21` | result: exit 1, ModuleNotFoundError: No module named 'yaml' | new fact: the failure reproduces locally
   verdict reading-errors: ModuleNotFoundError: No module named 'yaml' at export/config.py:3 | category: not installed | first check: which interpreter runs
2. action: `.venv/bin/pip show pyyaml` | result: Name: PyYAML, Version: 6.0.1 | new fact: pyyaml is installed in .venv
3. action: `.venv/bin/pip install pyyaml` | result: Requirement already satisfied: pyyaml | new fact: none
4. action: `python -m export.nightly --date 2026-09-21` | result: exit 1, ModuleNotFoundError: No module named 'yaml' | new fact: none
   stuck: making sure the package is installed -> find which interpreter the job runs
5. action: `python -c "import sys; print(sys.executable)"` | result: /usr/bin/python3 | new fact: plain python is the system interpreter, not .venv
6. action: `git log -p --since=2026-09-18 -- deploy/crontab` | result: 2026-09-21 commit a41c2e0 changed .venv/bin/python to python | new fact: the cron line lost the .venv interpreter on Monday
   verdict hypothesis-loop: H2 confirmed at step 6: the cron line runs the system python since commit a41c2e0
7. action: `git log --since=2026-09-10 -- requirements.txt` | result: no commits | new fact: no dependency changed recently
8. action: edit deploy/crontab line 1 back to `.venv/bin/python -m export.nightly` | result: one line changed | new fact: the cron line calls .venv again
9. action: `.venv/bin/python -m export.nightly --date 2026-09-21` | result: exit 0, wrote out/2026-09-21.csv, 1188 rows | new fact: the job succeeds with the .venv interpreter

## Done

observed at step 9: exit 0 and out/2026-09-21.csv written with 1188 rows
```

## The answer

```
The job fails because commit a41c2e0 on Monday changed the cron line from
.venv/bin/python to python, so it runs the system interpreter, where pyyaml
is not installed (steps 5 and 6). I changed deploy/crontab line 1 back to
.venv/bin/python. Running the job's command with that interpreter for
2026-09-21 exits 0 and writes out/2026-09-21.csv with 1188 rows (step 9).

## Done when
The cron line's command, run by hand with --date 2026-09-21, exits 0 and
writes out/2026-09-21.csv: observed at step 9.

## Not done
- The cron change is committed locally, not deployed.
- The pandas FutureWarning in the job log (scope out).
- Commit a41c2e0's message does not say why it changed the interpreter;
  its author may have had a reason.

## Unverified
none

## Checks
OK: PASS=12 WARN=1; exit 0. The warning is steps 1 and 4, the same run with
check_change: OK: PASS=6 INFO=1; exit 0
the same result, which is the loop that step 4's stuck line broke.
```
