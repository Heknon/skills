# Notes

**What they are:** short working notes kept from the first step: what was
asked, what done looks like, what you assume, what you tried, what came
back, and what you learned. For a short task they can live in your
messages. For a long one, keep them in a file outside anything you will
commit, so they survive and can be reread.

## Why

A weak spot of every model is that it cannot see its own repetition. Notes
turn a loop into something on the page: the same action twice, two steps
that taught nothing, an undo followed by the same redo. The loop rules in
`SKILL.md` are read off them. They also carry the goal across a long task,
so the goal is reread, not remembered.

## A shape that works

```
goal: <the ask, in the person's words, one line>
kind: <answer | change | decision | plan>
done when: <an observable condition, from core/scope.md>
budget: <n> steps, from core/scope.md
scope out: <things near the task that you will not touch, or none>
skill: <the skill whose description names the task, and the file it routes to, or none>

assumptions:
- A1 [unverified] <something you take as true and have not observed>

hypotheses:
- H1 [open] <cause> | test: <cheapest observation> | disproved if: <what you would see if it is wrong>

steps:
1. <what you did, exactly> -> <what came back> -> <what you learned, or nothing new>
   stuck: <the approach so far> -> <the new approach>
   verdict <procedure>: <decision and reason>

decided for you:
- <a choice that was the person's, and why you made it>

done: <observed at step n: what was seen> | <stopped at step n: why>
```

## What makes them useful

- **Actions are exact.** A command as you ran it. A read names the file
  and the part. A search names the pattern and where.
- **Results are copied, not paraphrased.** Error text especially.
- **"What you learned" is honest.** Rereading something you already knew
  is `nothing new`. Two of those in a row is a loop rule.
- **Statuses change, lines stay.** An assumption that proved false is
  marked `false at step n`, not deleted. It is the most valuable line.
- **One line per step.** Notes that take longer to write than the step
  are too long.
