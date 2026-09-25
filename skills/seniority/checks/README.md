# Checks

Two scripts that judge the work mechanically. Run the ledger check after
step 1, before any risky command, and at Finish. Run the change check at
Finish if you changed any file. Paste each one's last line into the answer
under *Checks*. Standard library only, Python 3.8 or later.

| Script | Reads | Rules |
| --- | --- | --- |
| `check_change.py --before .ledger/before --after . [--json]` | the snapshot of each file before its first edit, and the working directory | snapshot-present, files-changed (INFO), files-deleted, public-signature, swallowed-errors, test-expectations, module-constants (WARN), tests-added (INFO) |
| `check_ledger.py --ledger FILE [--json]` | a ledger written from `core/ledger.md` | header, done-when-observable (WARN), steps-numbered, repeated-action, oscillation, no-new-fact-streak, stuck-changes-approach, budget, risky-needs-challenge, hypotheses-falsifiable, assumption-status, done-observed, unverified-at-done (WARN) |

Every rule prints `PASS`, `FAIL`, `WARN`, `SKIP` or `INFO`, a count, up to
five offenders and a note that names the rule's source. `--json` prints the
same as one JSON object. The last line is the summary, for example
`OK: PASS=13; exit 0`.

## Exit codes

`0` when no rule is `FAIL`. `1` when any rule is `FAIL`. `WARN` and `INFO`
never change the exit code; read them anyway. `2` is an argument or read
error.

## What it cannot see

The checker compares action text. It cannot tell that two differently
worded actions are the same approach, that a `new fact` is really new, or
that an edit weakened a test. Risky commands are found by pattern: `prod`,
`production`, `deploy`, `publish`, `truncate`, `git push`, `rm -r`,
`--force`, `drop table`, `kubectl delete` or `apply`, `terraform apply` or
`destroy`, `helm install`, `upgrade` or `uninstall`, inside backticks or
after a leading `run`. It catches what leaves a mark on the page; the rules
in `SKILL.md` still apply to what does not.

The change check reads Python files with the `ast` module and test files
as text. It sees renamed, removed or re-defaulted public functions and
parameters, new `except` blocks that do not re-raise, and test lines with
`assert`, `expect`, `should` or `verify` removed or changed. It does not
see a function that returns a different value, or changes in other
languages' signatures: those still need old and new run on the same
inputs.

## A `FAIL` at Finish

Fix the ledger only where it misrecords what happened, such as a missing
step number or a status without a step. A `FAIL` because you really did
loop stays. The answer says so under *Checks*.

## Fixtures

`fixtures/change/` holds a snapshot, a good change (a fix plus a new test)
and a bad one (a renamed parameter, a changed default, a swallowed error,
a changed expectation, a changed constant). `fixtures/` holds three passing ledgers (`good.md`, finished;
`in_progress.md`, not finished; `risky_good.md`, a risky command after a
challenge and the person's answer), the unfilled template, and one failing ledger per loop or
format rule (`*_bad.md`). `sh fixtures/run_fixtures.sh` runs all of them,
then extracts the ledger from each `examples/*.md` with
`fixtures/extract_golden.py` and checks it. It also checks that each
example's answer quotes the summary line the checker really prints. It
prints `HARNESS PASS` when the good runs exit 0, the bad ones exit 1, and
every quote matches. Run it after editing the checker, an example, or the
ledger format.
