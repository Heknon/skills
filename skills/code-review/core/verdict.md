# Verdict: can it merge

**Verdict you produce:** exactly one of four, with its reason, first in
the answer.

```
## Verdict
changes needed: 1 blocker (GET /books/{id} answers 500 for a book with no reviews), and CI fails (ruff B006, E501)
```

## The four verdicts (CR2)

| Verdict | When |
| --- | --- |
| `approve` | tools and tests ran on the change and are clean; no findings, or nits you choose not to raise |
| `approve with comments` | tools and tests ran and are clean; only minors and nits |
| `changes needed` | any blocker or major; or a new error in a tool CI runs; or tests fail on the change; or it does not merge |
| `cannot judge` | the change is incomplete (a patch that does not apply, a missing file); or the tools or tests could not run and the change needs them to be trusted; or the scope left out a file that decides it |

## Deciding

1. **Anything that forces `changes needed`?** A blocker, a major, a
   new tool error or a failing test on the change. Then that is the
   verdict, whatever else is true.
2. **Did the checks run?** Nothing ran: never `approve` (invariant 3).
   Say what could not run and why; choose `cannot judge` when the
   change's correctness rests on what did not run (a query change with
   no database, a tested path that was skipped), or `approve with
   comments` naming the gap when it does not.
3. **Only minors and nits**: `approve with comments`. None: `approve`.
4. **The reason names the deciding findings**: their severity and a few
   words each, and the tool that fails if one does. Never "some issues".

## Never

- Never end without a verdict, even when asked only "what do you
  think?": the verdict is the answer to that too.
- Never soften the verdict because the change is small, urgent or the
  author senior; never harden it to look thorough.
- Never make the verdict depend on the MR description; the diff and the
  runs decide. "No behaviour change" is a claim: `review_diff.py defs`
  compares every signature, default and raise across a move.
