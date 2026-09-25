# Asking and stopping

**Verdict you produce:** one message to the person, either a question or a
stop report; or, in an unattended run, a decision written down in its
place. In your notes: the question and its answer as a step, or
`done: stopped at step <n>: <why>`.

## When to ask

- A **decision the person owns**: what matters more, how much risk to take,
  which of two valid behaviours they want.
- A **fact only they have**: their intent, a credential, access, history
  that is not written anywhere.
- **Two readings** of the ask that lead to different work, and one cheap
  look cannot settle it.
- An **irreversible or outward-facing** action they have not approved.
- A procedure's **stop and ask** branch.

## When not to ask

- The answer is in the environment, one or two tool calls away. Look first.
- You want reassurance. If the evidence decides, act on it.
- You have already asked this and they answered. Use the answer.

## How to ask

One message. The person should be able to answer without scrolling back.

```
<one line: what you are doing and where you are>
<the question>
Options: <a>, <b>. I recommend <a> because <fact>.
Meanwhile I will <what you do while waiting>, or: I am blocked until you answer.
```

At most three questions in one message, each with options and a
recommendation.

## How to stop

When you stop without finishing, report in this order:

```
Known: <facts, each with its step or path>
Not known: <what is missing>
Would settle it: <the observation, access or decision that would>
Recommend: <next action, and who takes it>
```

Then the closing headings from `SKILL.md`.

## When nobody will answer

In an unattended run (`SKILL.md`), a question is never sent and waited on.

- **A decision the person owns:** take the option you would have
  recommended, if it can be undone. Write it under *Decided for you* with
  the reason and what the other option was.
- **An irreversible or outward-facing step:** do not take it. Prepare it:
  the exact command, the challenge (`core/challenge.md`), what breaks
  between steps. Set it aside under *Decided for you* as waiting for a
  person, and go on with work that does not depend on it.
- **A fact only the person has:** proceed on the most likely reading,
  written as an unverified assumption, and choose work that stays correct
  if the assumption is wrong. If no such work exists, set the item aside.
- **Stuck on an item:** set it aside with the stop report above, and move
  to the next item. The run ends only when every item is done or set
  aside.

## Never

- Never ask an open question ("what should I do?") when you can offer
  options.
- Never stop with only "I could not do it". Say what you know.
- Never ask for permission to guess. Ask for the fact.
