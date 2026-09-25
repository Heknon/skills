# The ledger

**What it is:** one Markdown file per task, written before the first action
and updated after every step. It holds the goal, how you will know you are
done, what you assume, what you tried, what came back, and what you learned.
`checks/check_ledger.py` reads it, so keep the shapes below exactly.

## Why

A weak spot of every model is that it cannot see its own repetition. The
ledger turns a loop into something on the page: the same action line twice,
two `none` in a row, a budget passed. The loop rules in `SKILL.md` are read
off it. It also carries the goal across a long task, so the goal is reread,
not remembered.

## The template

Copy this block, fill every `<...>`, and delete nothing.

```markdown
# Ledger

goal: <the ask, in the person's words, one line>
done when: <an observable condition, from core/scope.md>
budget: <n> steps
scope out: <things near the task that you will not touch, or none>

## Assumptions

- A1 [unverified] <something you take as true and have not observed>

## Hypotheses

none

## Steps

1. action: <what you did, exactly> | result: <what came back> | new fact: <what you now know, or none>

## Done

not yet
```

## The rules for each line

**Header.** `goal:`, `done when:`, `budget:` and `scope out:` each on one
line. `budget:` is a whole number followed by `steps`.

**Assumptions.** One per line: `- A<n> [<status>] <text>`. The status is
one of:

- `unverified`
- `verified at step <n>`
- `false at step <n>`

When an assumption turns out false, keep the line and change the status.
Never delete one.

**Hypotheses.** Written by `core/hypothesis-loop.md`, or the single word
`none`. One per line:

```
- H<n> [<status>] <cause> | test: <the cheapest observation that tells> | disproved if: <what you would see if it is wrong>
```

The status is `open`, `confirmed at step <n>`, or `ruled out at step <n>`.

**Steps.** Numbered from 1, no gaps, one line each:

```
<n>. action: <action> | result: <result> | new fact: <fact or none>
```

- **action**: exact. A command goes in backticks as you ran it. A read
  names the file and the part: `read src/app.py lines 40-80`. A search names
  the pattern and where: `search "def load_config" in src/`. A question to a
  person is `action: ask: <question>`, and its result is their answer.
- **result**: what came back, short, with any error text copied exactly,
  not paraphrased. `exit 1, ModuleNotFoundError: No module named 'yaml'`.
- **new fact**: one fact you did not have before this step, or `none`.
  Rereading something you already know is `none`.

Lines indented under a step add to it. Three kinds are read by the checker:

```
   stuck: <the approach so far> -> <the new approach>
   budget extended to <n>: <reason>
   verdict <procedure>: <the verdict line the procedure told you to write>
```

**Done.** `not yet` while working. At the end, from `core/done.md`:

```
observed at step <n>: <what was seen that meets done when>
```

or, when stopping without finishing:

```
stopped at step <n>: <why>
```

## What the checker judges

| Rule | Fails when |
| --- | --- |
| `header` | a header line is missing or still holds a `<placeholder>` |
| `steps-numbered` | steps skip a number, or a step lacks `action`, `result` or `new fact` |
| `repeated-action` | the same action with the same result appears three times (twice is a `WARN`) |
| `oscillation` | the last four actions go A, B, A, B |
| `no-new-fact-streak` | two steps in a row say `new fact: none` and neither carries a `stuck:` line |
| `stuck-changes-approach` | the step after a `stuck:` line repeats an action from before it |
| `budget` | there are more steps than the budget and no `budget extended` line before the overrun |
| `hypotheses-falsifiable` | a hypothesis has no `disproved if:` |
| `assumption-status` | an assumption's status is not one of the three forms |
| `done-observed` | the Done section names a step that does not exist |
| `unverified-at-done` (`WARN`) | the task is done and assumptions are still `unverified`; list them under *Unverified* |

Two actions are the same when their text is the same after lower-casing and
collapsing spaces. Changing only a comment or the order of flags is still
the same action, and the checker cannot see that, so the rule is yours to
keep beyond what it catches.
