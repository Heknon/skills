# Challenge

**Verdict you produce:** `proceed`, `proceed with a change`, or `drop`,
and the question that decided it:

```
verdict challenge: <proceed | proceed with a change: <change> | drop> because <question number>: <answer>
```

Use it before acting on a plan of more than three steps, before accepting
an idea (yours or the person's), and before reporting a conclusion. Once
per plan or conclusion; again only when a new fact arrives.

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

## Deciding

- Question 4 or 5 names something cheap to check: check it first, then
  decide.
- Question 1 or 2 names a failure that is likely and costly: **proceed with
  a change** that removes it, or **drop**.
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
