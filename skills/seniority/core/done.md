# Done

**Verdict you produce:** the *done* line of your notes and the closing
headings of the answer: *Done when*, *Not done*, *Unverified*, *Decided
for you*. Done or not done, with the reason.

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
5. **Which assumptions are still unverified?** Update every status in your
   notes first. Only lines still `[unverified]` go under *Unverified*;
   verified and false ones do not.
6. **Describe the result from the files and your notes, not from
   memory.** Reread the diff before you describe a change. Reread your
   notes before you describe what you did: every step in them happened,
   and the answer never says you did not do a step they show.
7. **Compare before and after.** For every file you changed, look at the
   difference. A renamed or removed public function, parameter or
   command-line option, a changed default, a new `except` that does not
   re-raise, or a changed test expectation is a behaviour change: revert
   it, unless the goal asks for exactly that change. For a cleanup or
   refactor, run the old and the new code on the same inputs and compare
   the outputs (`core/scope.md` question 6).

## Verdict

In your notes: `done: observed at step <n>: <what was seen that meets
done when>`, or `done: stopped at step <n>: <why>`. Then the answer ends
with the closing headings from `SKILL.md`.

## Never

- Never write "should work", "ought to", or "I believe this fixes it" as
  the result. Either it was observed or it is not done.
- Never mark a test as passing by skipping it, deleting it, or changing
  what it expects without a reason from the goal.
- Never bury a failure in a summary. A failed check is the first line, not
  the last.
- Never claim done with a check that was not run.
- Never leave off the closing headings, even for a one-line answer or a
  question back to the person.
