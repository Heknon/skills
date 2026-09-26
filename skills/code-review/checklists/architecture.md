# Architecture

Run when the change adds or moves a route, a service, a repository, a
model at a boundary, a transaction or an exception class
(`core/checklist.md`). The architecture skill owns the layering rules
and their stable IDs, L1 to L11 (`checklist/violations.md`); this pass
runs its procedure on the changed files and ranks what it finds. It
never restates a rule's reasons: cite the ID.

## Steps

1. **The structure card first**: architecture `core/recognise.md`. What
   the card allows is not a finding: a crud-per-feature codebase that
   keeps simple checks in routes has no L2 finding for one more.
2. **Its searches, on the files the diff touches**: architecture
   `checklist/finding.md` ("The searches"). Report only hits on lines
   the change adds or changes. A violation that was there before goes
   in the answer as *seen before this change*, outside the verdict.
3. **Open every hit** and decide. Its "What the searches miss" table
   says what to read by hand; L2 is almost always read, not searched.
4. **Rank with this skill's scale.** Start from the ID's suggested
   severity in `violations.md`, apply its "Raise to" column only when
   you can write that scenario for this change, then check it against
   `core/rank.md`.
5. **Suggest the target shape by name**, never write it:
   architecture `shapes/L<n>-*.md` is the after; the refactoring skill
   performs it, in its own change.

## What outranks what

A layering ID says where code lives; the scenario says what goes wrong.
When one line carries both, the finding is ranked by the scenario:

| On one line | Rank |
| --- | --- |
| a database model returned, with a hidden field (L3) | blocker (security SEC2), L3 cited |
| a query in the route (L1) with no second caller yet | minor |
| a split transaction that can half-apply money (L5) | blocker |
| an untranslated database error caught broadly into a success (L8) | blocker (errors ERR1) |
| a service importing FastAPI (L4) with no other caller | minor |

(*lab:* a new route with `await User.find_one(` and `-> User` hit
architecture's L1 and L3 searches on the same lines; the stored
`password_hash` in its response made it a blocker.)

## Never

- Never rewrite the code into the target shape during the review.
- Never raise an ID's severity without a scenario for this change.
- Never report a card exception as a finding.
