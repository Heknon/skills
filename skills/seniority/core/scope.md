# Scope

**Verdict you produce:** the four header lines of the ledger: `goal`,
`done when`, `budget` and `scope out`.

Most wasted work is work on the wrong thing: a fix when an answer was
asked, a rewrite when a line was asked, a polished result for a question
nobody asked. Scope is fixed before the first action, and reread at every
Stuck and at Finish.

## Questions

1. **What were the person's exact words?** Copy them. If they are long,
   shorten by cutting, not by rewording: keep every noun and verb that
   limits the work. That is `goal`.
2. **What kind of result was asked?** One of:
   - an **answer** (a question: "why", "what", "where", "does it");
   - a **change** (code, config, a file);
   - a **decision** (pick between options);
   - a **plan** (what should be done, not doing it).

   A question is not a request to change anything. Answer it, then offer
   the change.
3. **What would the person look at to accept the result?** Write it as
   something you can observe in this environment. That is `done when`.
   Good forms:
   - a command and the result it must give: `` `pytest tests/test_api.py` exits 0 ``;
   - a file or section that must exist with a named content;
   - a question answered, with each claim pointing at a file, a command, or
     an output.
4. **What is near the task but not asked?** A second bug in the same file,
   an old dependency, an ugly name. Write them in `scope out`. You will
   report them; you will not fix them.
5. **How big is it?** Pick the budget from the table. It is a tripwire, not
   a target.

   | Task | Budget |
   | --- | --- |
   | answer from material you can read now | 8 steps |
   | one change in one place | 15 steps |
   | find the cause of a failure | 25 steps |
   | a change across several files or components | 40 steps |

6. **Is the change ask vague?** "Clean up", "improve", "refactor",
   "tidy", "modernise" name no observable result. Then `done when` always
   includes **behaviour unchanged**: the same public names, the same
   parameter names, the same return values and the same errors. Check it
   by running the old and the new code on the same inputs and comparing
   the outputs, including edge values: a whole number, zero, a negative, an
   empty value, `None`, a missing file. Tests that exist count only for
   what they cover. Anything that would
   change behaviour, even a clear improvement, is a finding under *Not
   done*, not an edit. Then either ask what the person wants from the
   cleanup, with options and a recommendation, or proceed on the narrowest
   reading, written as `A1 [unverified] the person means <reading>`.
7. **Can `done when` be met without changing something shared?** A
   script, a default, a config that other people or jobs also use. If the
   goal can be met by how you run it (a flag, an argument, an environment
   variable for this run), do that. Changing the shared thing is a
   trade-off (`core/trade-offs.md`, blast radius), and is offered, not done.
8. **Does it need anything irreversible or outward-facing?** Deleting,
   overwriting, pushing, sending a message, migrating data, spending money.
   Write each as an assumption line `A<n> [unverified] the person approves
   <action>`. Each passes gate 2 in `SKILL.md` before it runs, even if the
   person asked for it. `done when` for such an ask is the challenge shown
   to the person and their answer recorded; the risky action itself joins
   `done when` only after they answer.

## Verdict

```
goal: <the person's words, cut, not reworded>
done when: <observable condition>
budget: <n> steps
scope out: <list, or none>
```

## Never

- Never take the first action before `goal` and `done when` are written.
- Never write `done when: it works`, `it is fixed`, `it is correct` or
  `it is clean`. Those are predictions, not observations.
- Never replace the person's goal with a better one you thought of. Offer
  the better one under *Not done*.
- Never read "and anything else you notice" into a narrow ask.
- Never change a shared script, default or config to make your one run
  pass when the run itself can be changed instead.

## Stop and ask

- The words allow two readings that lead to different work, and one cheap
  look cannot tell which. Ask one question with both readings and your
  recommendation (`core/asking.md`).
- One reading is clearly more likely: do not ask. Proceed on it and write
  it as `A1 [unverified] the person means <reading>`.
- You cannot write any observable `done when`. Say what you can observe and
  ask whether that is enough.

## Examples

| Ask | Kind | done when |
| --- | --- | --- |
| "Why does the nightly job fail?" | answer | the cause named, with the log line and the code line that show it |
| "Fix the nightly job" | change | the job's command, run locally, exits 0 on the input that failed |
| "Should we use Redis or Postgres for the queue?" | decision | one option chosen, each rejected one with the fact against it |
| "Make the API faster" | change, vague | the endpoint's measured p95 before and after, on the same input; the target asked for (see Stop and ask if there is none) |
| "Tidy up the parser module" | change, vague | the agreed tidy-up applied, and every public name, parameter name, return value and error unchanged, shown by running the tests before and after |
| "Get the deploy script working" | change | the script, run with the flag or setting it needs, exits 0; a change to the script itself only if the person agrees |
