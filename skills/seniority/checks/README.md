# Checks

Scripts that judge the work mechanically. At Finish, run only
`check_finish.py` from the working directory: it runs the others and
checks the answer. Run `check_ledger.py` alone after step 1 and before
any risky command. Standard library only, Python 3.8 or later.

| Script | Reads | Rules |
| --- | --- | --- |
| `check_finish.py [--dir .] [--json]` | `.ledger/ledger.md`, `.ledger/answer.md`, `.ledger/before/`, `.ledger/probe.py` | the ledger rules; the change rules when the kind is `change` or a snapshot exists; probe-present, probe-runs, behaviour-unchanged when the goal is a cleanup, refactor, tidy-up or improvement, or `done when` says unchanged, or a probe exists; answer-present, answer-headings, answer-done-matches-ledger, answer-unverified-matches, answer-quotes-checks. Prints a `ledger:`, `change:` and `probe:` line to quote, then `FINISH OK` or `FINISH NOT OK` |
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

`fixtures/finish/` holds three finished tasks: `good` (a tidy-up whose
probe gives the same output before and after, and a correct answer),
`bad_behaviour` (the probe's output changes, and the answer quotes stale
lines) and `bad_answer` (no closing headings). `fixtures/change/` holds a snapshot, a good change (a fix plus a new test)
and a bad one (a renamed parameter, a changed default, a swallowed error,
a changed expectation, a changed constant). `fixtures/` holds three passing ledgers (`good.md`, finished;
`in_progress.md`, not finished; `risky_good.md`, a risky command after a
challenge and the person's answer), the unfilled template, and one failing ledger per loop or
format rule (`*_bad.md`). `sh fixtures/run_fixtures.sh` runs all of them,
then extracts the ledger from each `examples/*.md` with
`fixtures/extract_golden.py` and checks it, then runs the finish check on
the example's ledger and answer, which proves the answer's headings and
its quoted ledger line. It
prints `HARNESS PASS` when the good runs exit 0, the bad ones exit 1, and
every quote matches. Run it after editing the checker, an example, or the
ledger format.
