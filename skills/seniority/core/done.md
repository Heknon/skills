# Done

**Verdict you produce:** the *Done* section of the ledger and the four
closing headings of the answer: *Done when*, *Not done*, *Unverified*,
*Checks*. Done or not done, with the reason.

"It should work now" is the most common false statement a model makes.
Done is an observation, not a feeling.

## Questions

1. **Reread `goal` and `done when`.** Was `done when` observed in this task?
   At which step? If you only predicted it, run it now. If you cannot run
   it, the task is not done: say so.
2. **Did the check exercise the change?** The test that passed ran your
   case (its name is in the output); the command ran the file you changed;
   it ran in the environment the goal is about. A check that passes without
   touching the change proves nothing.
3. **Read your own result as a reviewer who wants to reject it.** Look for:
   - changes outside the goal;
   - a test, check or assertion weakened, skipped or deleted to get a pass;
   - an error caught and ignored;
   - debug output, commented-out code, temporary files left behind;
   - values hard-coded to fit the one case you tried;
   - secrets, tokens or personal data in code, output or examples;
   - a statement in the answer at the level recalled or guessed, stated as
     fact (`core/evidence-levels.md`).

   Then read the whole of every file you changed, not only your lines.
   Every other defect you see there goes under *Not done*, unfixed.

   Fix what you find in your own change, then return to question 1.
4. **What was asked and not done?** And what did you find and leave, from
   `scope out`? Both go under *Not done*.
5. **Which assumptions are still unverified?** Update every status in the
   ledger first. Only lines still `[unverified]` go under *Unverified*;
   verified and false ones do not.
6. **Describe the result from the files and the ledger, not from
   memory.** Reread the diff before you describe a change. Reread the
   ledger before you describe what you did: every step in it happened, and
   the answer never says you did not do a step the ledger shows.
7. **Write the answer to `.ledger/answer.md` and run
   `python3 checks/check_finish.py`** from the working directory (gate 3
   in `SKILL.md`). A `FAIL` in the change part is a behaviour change:
   revert it, unless the goal asks for exactly that change. A `FAIL` in
   the probe part is a result that changed: revert it, or keep the old
   behaviour and propose the new one under *Not done*. A `FAIL` in the
   ledger part that reflects a real gap is fixed in the ledger; a `FAIL`
   because you really did loop stays, and the answer says so. A `FAIL` in
   the answer part is fixed in the answer. Run it again until it prints
   `FINISH OK`, then send the answer file's text unchanged.

## Verdict

In the ledger:

```
## Done

observed at step <n>: <what was seen that meets done when>
```

or `stopped at step <n>: <why>`. Then the answer ends with the four
headings from `SKILL.md`.

## Never

- Never write "should work", "ought to", or "I believe this fixes it" as
  the result. Either it was observed or it is not done.
- Never mark a test as passing by skipping it, deleting it, or changing
  what it expects without a reason from the goal.
- Never bury a failure in a summary. A failed check is the first line, not
  the last.
- Never claim done with a checker that was not run.
- Never leave off the four closing headings, even for a one-line answer
  or a question back to the person.
