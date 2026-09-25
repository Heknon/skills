# Template: decision record (ADR)

One decision per record, numbered in order, never rewritten after it is
accepted: a later decision supersedes it with a new record.

```markdown
# <number>. <decision, as a short phrase>

Date: <YYYY-MM-DD>
Status: <proposed | accepted | superseded by [NNNN](NNNN-title.md)>

## Context

<The situation and the forces, as they were then.>

## Decision

<What was decided, in one or two sentences.>

## Alternatives considered

- <option>: <why not, as recorded>

## Consequences

<What becomes easier and harder.>
```

Everything in it comes from the people who decided, or from records
(issues, pull requests, meeting notes). When writing one for an old
decision, fill only what a record says, and write `not recorded`
elsewhere.
