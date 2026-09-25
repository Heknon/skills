# Template: explanation

For someone who wants to understand how and why. Prose and diagrams, no
steps.

```markdown
# <How X works> / <Why X is designed this way>

<One paragraph: the question this page answers.>

## <The parts, or the flow>

<Prose, with one diagram if it helps. Each claim backed by code.>

## Reasons

<Each reason with where it comes from (ADR, commit, issue, person), or
"Reason: not recorded".>
```

Describe what the code does and what follows from it ("a cached answer
can be up to one hour old"). Never write what it is for ("to balance
freshness and performance", "to reduce load") unless a record says so;
that is a reason, and belongs under *Reasons* with its source. No
*Trade-offs* section unless a record names the trade-offs.
