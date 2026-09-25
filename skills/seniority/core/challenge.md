# Challenge

**Verdict you produce:** `proceed`, `proceed with a change`, or `drop`,
and the question that decided it:

```
verdict challenge: <proceed | proceed with a change: <change> | drop> because <question number>: <answer>
```

Use it before acting on a plan of more than three steps, before accepting
an idea (yours or the person's), before reporting a conclusion, and always
before any action that cannot be undone or reaches
outside this environment, even one the person asked for. Once per plan or
conclusion; again only when a new fact arrives.

## The five questions

Answer each in one concrete line. "There may be issues" is not an answer.
Name the issue.

1. **Pre-mortem.** It is a week later and this failed. What is the most
   likely reason?
2. **Counter-case.** Name one concrete input, situation or user for which
   this is wrong.
3. **Simplest alternative.** What is the smallest thing that meets
   `done when`? If this plan is bigger, what does the extra buy?
4. **Load-bearing assumption.** Which assumption, if false, sinks this? Is
   it verified? If not, can one step verify it?
5. **What would change your mind?** Name the observation that would make
   you drop this. If you can get it cheaply, get it now, before acting.

## Questions that find the risk in a plan

For a plan of several steps, before question 1, read the steps in order and
ask of each: **what is true of the system right after this step, before the
next one?** A plan that is right at the end can be broken in between: a
column renamed before the code that reads it is changed, a service
stopped before its replacement is up, a file deleted before its copy is
checked.

Answer it from a search, not from reading the plan: take the name the step
changes (the column, the file, the flag, the endpoint, the function) and
search the code, configs and scripts for everything that reads it. Every
reader not yet changed by an earlier step is broken in between. Write:

```
verdict challenge-steps: after step <n> and before step <m>: <each reader that breaks, with its path>
verdict challenge-steps: none: searched <name> in <where>, every reader is changed first
```

## Deciding

- Question 4 or 5 names something cheap to check: check it first, then
  decide.
- Question 1 or 2, or the step-by-step reading, names a failure that is
  likely and costly: **proceed with a change** that removes it, or **drop**.
  If the plan is the person's, the change is proposed to them first
  (`core/pushback.md`), and nothing irreversible runs until they answer.
- Question 3 shows a smaller way that meets `done when`: take the smaller
  way, unless the person asked for the bigger one.
- None of the above: **proceed**.

## Challenging a conclusion

Before reporting "the cause is X" or "X is true", add a sixth question:

6. **What else would produce exactly these observations?** If something
   else would, the conclusion is not proven. Write it as a second hypothesis
   in `core/hypothesis-loop.md` and find the observation that separates the
   two.

## Challenging the person's idea

Ask the same questions of an idea the person proposed. If the answers show
it will not meet their goal, and you have evidence at the level observed or
read, go to `core/pushback.md`. If you only have a doubt, say the doubt in
one line and proceed with their idea.

## Never

- Never skip the challenge because the plan feels obvious. The obvious plan
  is the one that was not checked.
- Never challenge the same plan twice without a new fact. That is a loop.
- Never turn the challenge into a list of every conceivable risk. Five
  lines, one each.
