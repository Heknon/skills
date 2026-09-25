# Trade-offs

**Verdict you produce:** the chosen option with a one-line reason, and each
rejected option with the one fact against it:

```
verdict trade-offs: <chosen> because <fact>; not <option> because <fact>; not <option> because <fact>
```

Two failures: choosing by taste, and never choosing. This procedure fixes
the questions, so the choice comes from facts, and caps the deliberation,
so it ends.

## Questions

Keep at most three options. Drop any option that is worse than another on
every question below before you start.

For each option, one line per question:

1. **Does it do what was asked, and only that?** An option that also does
   something else carries that something's risk.
2. **Can it be undone, and how?** Undone by reverting a file, by a
   command, by a person's work, or not at all.
3. **What does it touch besides the goal?** Files, other components, other
   people, stored data, anything outside this environment. This is the
   blast radius.
4. **What does it cost now?** Rough steps.
5. **What does it cost later?** What someone must maintain, remember, or
   work around.
6. **What evidence says it works here?** Use `core/evidence-levels.md`:
   observed, read, or only recalled.

## Choosing

Read top down; the first rule that separates the options decides.

1. An option that does not do what was asked is out.
2. An option that cannot be undone, or reaches outside this environment,
   is not chosen without the person (`core/asking.md`).
3. Prefer the option with the higher evidence level.
4. Prefer the smaller blast radius.
5. Prefer the lower cost later over the lower cost now.
6. Still tied: pick the simpler one, write "close call" in the verdict, and
   move on.

You may spend **one** step getting a fact to break a tie. If that step does
not separate them, rule 6 decides.

## Never

- Never choose because an option is more elegant, more interesting or more
  modern.
- Never list more than three options in the answer.
- Never reopen a decision without a new fact. A new doubt is not a new fact.

## Stop and ask

- The best option is irreversible or outward-facing.
- The options differ on something the person owns: speed against cost,
  risk against time, one team's needs against another's. State the
  difference in one line each and recommend one.
