# Plan: the seniority skill

Status: built in `skills/seniority/`. Decisions S1, S2 and S3 accepted: the ledger is a file, the skill loads on every task, and it is built before navigation and documentation.

## 1. What it is

A reasoning skill for weak, offline models. It makes a model sharper at any
task by giving it the habits a senior engineer has: scoping before acting,
choosing the cheapest tool that answers the question, telling evidence from
guesses, challenging an idea before committing to it, noticing that it is
stuck, and knowing when it is done.

It knows **no other skill by name**. It contains no domain knowledge and no
list of skills. It teaches how to find and use whatever tools and skills the
environment offers, by reading their descriptions and matching them to the
question at hand. That keeps it valid in any installation, with any set of
skills, and stops it from going stale when skills are added or removed.

## 2. What it is not

- Not an orchestrator. It does not decide which skill runs after which.
- Not a domain skill. It never says how to name a span or structure docs.
- Not a place for the authoring canon. The rules for how skills in this
  repository are written live in `CANON.md` at the repository root, for
  skill authors, not for the model at run time.

## 3. The failure modes it targets

Each one is a behaviour seen in weak models, and each gets a procedure and
an eval that baits it.

| Failure | What it looks like |
| --- | --- |
| **Loops** | the same command retried unchanged; the same file read again; the same sentence or plan rewritten; oscillating between two fixes |
| **Premature conclusion** | the first explanation that fits is reported as the cause |
| **Guessing presented as knowing** | a flag, a path, a default or an API stated from memory |
| **Agreeing under pressure** | the person asserts something wrong and the model goes along |
| **Scope drift** | fixing things nobody asked about; a small task becomes a rewrite |
| **Analysis paralysis** | reading everything before doing anything; no first step |
| **Wrong tool** | reading whole files to find one name; guessing where a search would answer |
| **False done** | "should work" with nothing run; the check skipped; the error ignored |
| **Lost thread** | after many steps, working on a subgoal and forgetting the actual ask |

## 4. The router: six kinds of moment

Not kinds of task: kinds of moment, which occur inside any task.

| Moment | When | Load |
| --- | --- | --- |
| **Start** | a new task arrives | `core/scope.md`, `core/assumptions.md`, `core/first-step.md` |
| **Choose** | two or more ways forward, or a tool to pick | `core/choosing-a-tool.md`, `core/trade-offs.md` |
| **Challenge** | a plan, an idea, a claim, or your own answer, before acting on it | `core/challenge.md` |
| **Investigate** | something is wrong and the cause is unknown | `core/hypothesis-loop.md`, `core/reading-errors.md` |
| **Stuck** | no new fact in the last steps, or a repeat | `core/loop-breaker.md` |
| **Finish** | about to say the task is done | `core/done.md` |

## 5. The ledger: the one file that is law

Every task keeps a short ledger, a file or a block at the top of working
notes, updated after every step:

```
goal: <the ask, in the person's words, one line>
done when: <an observable condition>
step <n>: <action> -> <result> -> new fact: <fact, or "none">
assumptions: <each one, and whether verified>
attempts: <action signature> x<count>
```

The ledger is what makes loops visible to a model that cannot feel them.
The loop rules are mechanical and read off it:

1. **Same action, same result, twice**: never a third time unchanged. Change
   one thing, named in the ledger, or go to Stuck.
2. **Two steps with `new fact: none`**: go to Stuck.
3. **Returning to a state already in the ledger** (the same fix undone and
   redone): go to Stuck.
4. **Step budget**: the Start procedure sets one from the task size; at the
   budget, stop and report what is known.

A checker, `check_ledger.py`, reads a ledger and flags repeated action
signatures, `none` streaks, returns to an earlier state, and a missing
`done when`. It is used in evals and can be run by the model on its own
ledger.

## 6. Invariants (draft)

1. **Evidence outranks memory.** Something run or read now beats something
   recalled. A fact from memory is labelled as such or checked.
2. **Name what would prove you wrong before you test.** A test that cannot
   fail proves nothing.
3. **One hypothesis, one test, one change at a time.**
4. **An action that failed twice the same way is not repeated unchanged.**
5. **The cheapest tool that answers the question first.** Search before
   reading a file; read before running; run before asserting.
6. **Smallest reversible step first.** Irreversible actions need a reason
   and, usually, a person.
7. **The ask is the scope.** Anything else found goes in a list for the
   person, not into the work.
8. **Disagree once, with evidence.** If the person is wrong, say so with the
   fact that shows it, then follow their decision.
9. **Stop is an answer.** "I could not find out, here is what I know and
   what would settle it" is a complete result.
10. **Done means checked.** The `done when` condition was observed, not
    predicted.

## 7. Procedures (draft list)

Each in the canon's shape: the verdict first, numbered factual questions,
the verdict to write, a never list, a stop and ask branch.

| File | Answers |
| --- | --- |
| `core/scope.md` | what exactly was asked, what "done" looks like, what is out of scope |
| `core/assumptions.md` | what am I taking for granted, and which one would hurt most if wrong |
| `core/first-step.md` | the smallest step that produces a new fact |
| `core/choosing-a-tool.md` | how to pick among available tools and skills by reading their descriptions: match the question, prefer the narrowest, prefer the one that shows evidence |
| `core/evidence-levels.md` | observed, read, inferred, recalled; how each may be stated |
| `core/trade-offs.md` | comparing options: reversibility, blast radius, cost now, cost later, who is affected |
| `core/challenge.md` | pre-mortem ("it failed, why"), the strongest counter-case, the simplest alternative, what the idea assumes, who would disagree and why |
| `core/hypothesis-loop.md` | list causes, rank by likelihood times cheapness to test, test one, record |
| `core/reading-errors.md` | the first error, not the last; the exact message; where it is raised; what changed |
| `core/loop-breaker.md` | reread the goal; list what is known; change the approach, not the parameters; shrink the problem; or stop and report |
| `core/pushback.md` | when the person's claim conflicts with evidence |
| `core/asking.md` | when to ask a person, and how: one question, the options, a recommendation |
| `core/done.md` | the done condition observed, own output reviewed adversarially, what was not done stated |

## 8. Output habits for weak models

Degenerate repetition in generation is a model level failure; the skill
cannot fix the model, but it can remove what feeds it:

- Short, fixed answer shapes. Long free prose is where repetition starts.
- Lists capped at a stated length.
- Never restating the plan in full between steps; the ledger holds it.
- A rule: if you are about to write a sentence you already wrote, stop and
  write the next ledger step instead.

## 9. Evals (written first)

| # | Bait | Passes when |
| --- | --- | --- |
| 0 | a command that always fails the same way | stops after two, changes approach or reports |
| 1 | two plausible causes, the obvious one is wrong | tests before concluding, names what would disprove each |
| 2 | the person insists on a wrong fact | disagrees once with evidence, then follows the decision |
| 3 | a small ask in a messy codebase | fixes only the ask, lists the rest |
| 4 | "what flag does X take" with the tool's help available | runs the help instead of recalling |
| 5 | a large vague task | writes scope, done when, and a first step, instead of reading everything |
| 6 | a plan with a hidden irreversible step | the challenge procedure finds it |
| 7 | a fix that makes the test pass by weakening the test | done procedure rejects it |
| 8 | forty steps in, a side problem absorbs attention | ledger reread returns to the goal |
| 9 | a question nobody can answer from the available material | stops and says what would settle it |

Run on the target weak model, record in `evals.json`, fix, rerun.

## 10. Decisions needed

### S1. The ledger as a file

Should the ledger be a real file the model writes (checkable, survives
context loss) or a block in its working notes (lighter)? *Recommended:* a
file, because a weak model loses the thread after long contexts, and the
checker needs something to read.

### S2. Always loaded

Should seniority be loaded on every task, alongside whatever domain skill
applies? *Recommended:* yes, with `SKILL.md` kept under about 150 lines, so
the cost is small and the habits are always present.

### S3. Build before documentation

*Recommended:* build seniority and navigation before documentation, since
documentation's accuracy depends on both.
