# Assumptions

**Verdict you produce:** the *Assumptions* list in the ledger, and the one
assumption to verify first.

Every task rests on things you have not checked. The dangerous ones are
the ones you do not notice you are making. Writing them down is how you
notice them; ranking them is how you decide which to check.

## Questions

1. **What are you taking as true that you have not observed in this task?**
   Go through the five sources, and write at least one line for each that
   applies:
   - **the environment**: which interpreter, which virtual environment,
     which version of a tool, which operating system, which directory;
   - **the code**: this is the file that runs, this function is the one
     called, this config is the one loaded;
   - **the tools**: this command exists, this flag means what you think;
   - **the person**: what they meant, what they already tried, what they
     allow;
   - **the diagnosis**: the cause the person or you named at the start.
2. **For each, if it is false, how much work is lost?** Little, some, or
   all of it.
3. **For each, how cheap is it to check?** One tool call, a few, or it
   needs a person.

## Verdict

Write every assumption as `A<n> [unverified] <text>`. Then order your work:

| If false, loses | Check costs | Do |
| --- | --- | --- |
| all or some | one call | check it now, before anything else |
| all | more | check it before the step that depends on it, or ask |
| some | more | leave it, and design the work so it does not depend on it |
| little | any | leave it `unverified`; it goes under *Unverified* at the end |

Write the check as a step. Then update the line to `verified at step <n>` or
`false at step <n>`. A false assumption is the most valuable line in the
ledger: reread `goal` and ask whether the plan still holds.

## The silent assumptions

These are made so often that they are worth checking by habit.

| Assumption | The one call that checks it |
| --- | --- |
| the file I am editing is the one that runs | find what imports or loads it; add nothing, just look |
| the interpreter running the code is the one I installed into | print its path from inside: `python -c "import sys; print(sys.executable)"` |
| the test I ran ran my case | read the test output for the case's name and the count collected |
| the error comes from my change | run the same thing on the code without the change |
| this tool's flag works as I remember | run the tool's `--help`, or read its docs in this environment |
| the docs I am reading match the installed version | print the version and compare with the one the docs name |
| the person's diagnosis is right | treat it as a hypothesis in `core/hypothesis-loop.md` |

## Never

- Never state an assumption as a fact in an answer. If it reaches the answer
  unverified, it goes under *Unverified*.
- Never verify by reasoning about it. Verify by looking.
- Never delete an assumption that turned out false. Mark it.

## Stop and ask

- An assumption about what the person wants, or allows, would lose all the
  work if false, and nothing in the environment settles it.
