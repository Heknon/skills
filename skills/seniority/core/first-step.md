# First step

**Verdict you produce:** step 1 in the ledger.

Two ways to fail at the start: act before knowing anything, or read
everything before doing anything. The first step is the smallest action
that produces the fact you most need.

## Questions

1. **Which one fact, if you knew it, would most change what you do next?**
   Usually one of:
   - where the thing named in the goal lives (a file, a function, a config);
   - whether the problem happens at all, here, now (reproduce it);
   - which of your assumptions is false.
2. **What is the cheapest action that produces that fact?** Use
   `core/choosing-a-tool.md`.
3. **Can it be done without changing anything?** Prefer the read-only
   action. A change comes after you know where and why.

## Verdict

Write the action as step 1, then do it.

## Rules by kind of task

- **Answer.** Search for the key noun of the question first. Read only
  what the search points at.
- **Change.** Find the exact place first, then find what calls it, then
  change it. For a bug, reproduce it before touching anything: a fix you
  cannot see failing before cannot be seen working after.
- **Decision.** Write the options and the one fact that would separate
  them. The first step gets that fact.
- **Plan.** Find what exists now before proposing what should exist.
- **Large and vague.** Find the entry point: the command that starts the
  program, the route that serves the request, the test that covers the
  area. Start there, not at the top of the tree.

## Never

- Never read a whole directory "to understand the codebase". Read what a
  search or an entry point leads you to.
- Never change code before you can see the problem it fixes.
- Never plan more than three steps ahead in detail. The result of step 1
  changes step 4.

## Stop and ask

- The first fact needs access you do not have, such as a production log or
  a credential. Say which fact, and why it comes first.
