# Asking and stopping

**Verdict you produce:** one message to the person, either a question or a
stop report. In the ledger: a step whose action is `ask: <question>`, or
`stopped at step <n>: <why>` under *Done*.

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

Then the four closing headings from `SKILL.md`.

## Never

- Never ask an open question ("what should I do?") when you can offer
  options.
- Never stop with only "I could not do it". Say what you know.
- Never ask for permission to guess. Ask for the fact.
