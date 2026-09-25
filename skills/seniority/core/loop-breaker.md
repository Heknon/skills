# Loop breaker

**Verdict you produce:** a `stuck:` line under the step where a loop rule
fired, naming the old approach and the new one:

```
   stuck: <the approach so far> -> <the new approach>
```

or a stop, with `stopped at step <n>: <why>` in the Done section.

You came here because a loop rule in `SKILL.md` fired. That is not a
failure; not noticing would be. Do the steps in order.

## Steps

1. **Reread `goal` and `done when`, word for word.** Is what you are doing
   still needed for them? Long tasks drift into side problems. If the
   current work is not needed for `done when`, drop it, write it under
   `scope out`, and go back to the goal.
2. **List what you know.** Copy every `new fact` that is not `none`. Read
   them together. The answer is often already there, split across steps
   you did not connect.
3. **Name the approach so far in one line.** For example: "running the
   test and editing the import", or "guessing config keys".
4. **Change the approach, not its parameters.** A different flag, a
   longer timeout, or the same edit in another spot is the same approach.
   A different approach looks like one of these:

   | You have been | Switch to |
   | --- | --- |
   | reading code and reasoning | running it and printing values |
   | running it and retrying | reading the code where it fails |
   | fixing the symptom | reproducing it smaller (`core/hypothesis-loop.md`) |
   | guessing a name, key or flag | finding it in the source, the help output, or the shipped defaults |
   | using one tool | another rung of `core/choosing-a-tool.md` |
   | working on the whole | one file, one test, one input |
   | alternating between two fixes | treating both as wrong: the cause is elsewhere; return to the hypothesis loop with both results as observations |

5. **Write the `stuck:` line** under the current step, and take the next
   step with the new approach. The step after a `stuck:` line must not
   repeat any action from before it.
6. **Budget.** If the budget rule fired: if the ledger's facts show real
   progress toward `done when`, extend it once with `budget extended to
   <n>: <reason>`. A second overrun, or no progress: stop.

## When to stop instead

Stop and report (`core/asking.md`) when any of these hold:

- you cannot name a different approach;
- this is the second `stuck:` line for the same problem;
- the budget ran out a second time;
- the next approach needs something only a person has.

Stopping with a clear report is a good result. Looping is not.

## Repeating yourself in writing

The same failure happens in prose. If you notice you are writing a
sentence, a list or a plan you already wrote, stop writing. Do not finish
the paragraph. Write the next ledger step instead, and take it.

## Never

- Never do the same action "one more time to be sure". The only exception
  is testing an intermittent failure, written as a step with a count:
  `` `pytest tests/test_x.py` run 10 times ``.
- Never start over and discard the ledger. The facts in it are the way out.
- Never answer a loop by thinking longer about the same approach.
