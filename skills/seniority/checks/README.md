# Checks

One script that judges a ledger mechanically. Run it at Finish, and any
time you suspect a loop. Paste its summary line into the answer under
*Ledger check*. Standard library only, Python 3.8 or later.

| Script | Reads | Rules |
| --- | --- | --- |
| `check_ledger.py --ledger FILE [--json]` | a ledger written from `core/ledger.md` | header, done-when-observable (WARN), steps-numbered, repeated-action, oscillation, no-new-fact-streak, stuck-changes-approach, budget, hypotheses-falsifiable, assumption-status, done-observed, unverified-at-done (WARN) |

Every rule prints `PASS`, `FAIL`, `WARN`, `SKIP` or `INFO`, a count, up to
five offenders and a note that names the rule's source. `--json` prints the
same as one JSON object. The last line is the summary, for example
`OK: PASS=12; exit 0`.

## Exit codes

`0` when no rule is `FAIL`. `1` when any rule is `FAIL`. `WARN` and `INFO`
never change the exit code; read them anyway. `2` is an argument or read
error.

## What it cannot see

The checker compares action text. It cannot tell that two differently
worded actions are the same approach, that a `new fact` is really new, or
that an edit weakened a test. It catches the loops that leave a mark on the
page; the loop rules in `SKILL.md` still apply to the ones that do not.

## A `FAIL` at Finish

Fix the ledger only where it misrecords what happened, such as a missing
step number or a status without a step. A `FAIL` because you really did
loop stays. The answer says so under *Ledger check*.

## Fixtures

`fixtures/` holds two passing ledgers (`good.md`, finished; `in_progress.md`,
not finished), the unfilled template, and one failing ledger per loop or
format rule (`*_bad.md`). `sh fixtures/run_fixtures.sh` runs all of them,
then extracts the ledger from each `examples/*.md` with
`fixtures/extract_golden.py` and checks it. It also checks that each
example's answer quotes the summary line the checker really prints. It
prints `HARNESS PASS` when the good runs exit 0, the bad ones exit 1, and
every quote matches. Run it after editing the checker, an example, or the
ledger format.
