# Ledger

goal: "the nightly export job fails, fix it"
kind: change
done when: `python -m export.nightly --date 2026-09-20` exits 0 and writes `out/2026-09-20.csv`
budget: 25 steps
scope out: the deprecation warning from pandas in the same run

## Assumptions

- A1 [false at step 3] the job runs in the project's .venv
- A2 [verified at step 2] the failure reproduces locally

## Hypotheses

- H1 [ruled out at step 4] yaml is missing from requirements | test: grep requirements.txt for pyyaml | disproved if: pyyaml is listed
- H2 [confirmed at step 5] the job runs with the system python, not .venv | test: print sys.executable inside the job | disproved if: it prints .venv/bin/python

## Steps

1. action: read the cron entry in `deploy/crontab` | result: `0 2 * * * python -m export.nightly` | new fact: the cron line calls plain `python`
2. action: `python -m export.nightly --date 2026-09-20` | result: exit 1, ModuleNotFoundError: No module named 'yaml' | new fact: the failure reproduces locally
3. action: `which python` | result: /usr/bin/python | new fact: plain python is the system interpreter, not .venv
4. action: search "pyyaml" in requirements.txt | result: requirements.txt:7 pyyaml==6.0.1 | new fact: yaml is declared, so H1 is ruled out
5. action: `python -c "import sys; print(sys.executable)"` | result: /usr/bin/python | new fact: the job's interpreter is the system one, H2 confirmed
   verdict hypothesis-loop: H2 confirmed at step 5: the cron line runs the system python
6. action: edit `deploy/crontab` line 1 to call `.venv/bin/python` | result: file changed, one line | new fact: none
7. action: `.venv/bin/python -m export.nightly --date 2026-09-20` | result: exit 0, wrote out/2026-09-20.csv, 1204 rows | new fact: the job succeeds under .venv

## Done

observed at step 7: exit 0 and out/2026-09-20.csv written with 1204 rows
