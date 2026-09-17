# Question to measurement

**Verdict you produce:** for a question a person asked, the measurement that
answers it, named as one of the patterns below, with the signal, the
instrument, the labels and the moment it is recorded. It goes into
`vocabulary.md` in the section for its signal, with the question written in
the *Changes* table so the reason survives.

Use this when the task starts from a question, such as "how long do
environments take" or "how many are stuck", rather than from a piece of code.
Answer the questions in order, find the pattern, and copy it. Do not design a
measurement that is not one of these patterns; that is a stop and ask.

## Questions

1. **Write the question as a sentence with a noun, a measure and a time.**
   "The ninety fifth percentile of environment duration, per day." If it has
   no measure, it is not a question yet. Ask the person for the number they
   would put on a chart.
2. **Is the noun a thing that ends?** An environment, a request, a job.
   If yes, answer question 3. If it never ends, such as a queue or a pool, go
   to pattern **Level**.
3. **Can the thing fail to end?** A crash, a hang, a lost message, a process
   killed. If yes, the measurement recorded at the end is blind to the case
   the person cares about most. Use pattern **Duration that may never end**.
   If it cannot fail to end, use pattern **Duration**.
4. **Is the measure a count, a rate, a distribution or a current value?**
   Count or rate: **Rate**. Distribution or a percentile: **Duration** or
   **Size**. Current value: **Level**.
5. **Is the question "did it happen at all"?** Use pattern **Absence**.
6. **Is the question about one occurrence?** "Why was this one slow." That is
   a trace question, not a metric. The answer is the unit's span with its
   children; go to `traces/`.

## Patterns

### Duration

For things that always end. Record once, at the end, into a **histogram**
with explicit buckets, labelled by the label tier only. Percentiles come
from the histogram. If the thing already has a span, this is **derived**;
emit nothing and read it from the transaction or span latency screen.

### Duration that may never end

Two measurements, because one moment cannot see both cases.

- **Closed:** the histogram from the Duration pattern, recorded at the end.
  Add a label `outcome` with values `completed` and `abandoned`.
- **Open:** an **observable gauge** whose callback runs at every export
  interval, walks the registry of things currently open, and reports per
  process:
  - `<namespace>.<noun>.open.count`, how many are open now,
  - `<namespace>.<noun>.open.age.max`, seconds since the oldest one started.
  Both combine across processes: sum the counts, take the max of the maxima.
  Never report a percentile from the callback; percentiles do not combine.
  Never put the instance id on the gauge; the max and the count say which
  process to look at, and the instance is found in the trace.
- **Abandonment:** when the process shuts down with things still open, close
  each one with `outcome=abandoned`, record its age into the histogram, and
  end its span with status `ERROR` and description `abandoned at shutdown`.
- **Staleness:** the alert is `open.age.max` greater than a multiple of the
  closed histogram's ninety ninth percentile. The threshold comes from the
  data, not from a guess.

A span alone cannot answer this question. The SDK exports a span when it
ends, so a span that never ends is never seen.

### Rate

How many per unit of time. A **counter**, labelled by the label tier,
incremented at the moment the thing happens. If the thing has a span, this is
**derived** from throughput; emit nothing. Never record a rate yourself; the
backend divides by time.

### Level

How many or how much right now. An **up down counter** when the code sees
every increment and decrement, an **observable gauge** when it is cheaper to
read the current value in a callback. Queue depth, connections open, memory.
Combine across processes by sum for counts and by max or by process for
capacities.

### Size

A distribution of a quantity that is not time: bytes, rows, items. A
**histogram** with buckets in the base unit. Same rules as Duration.

### Absence

"Did the nightly run at all." Nothing in the process can report its own
absence. The measurement is a **counter** incremented on success, and an
alert on the backend that fires when the counter has not moved for longer
than the expected interval. Write the alert rule into the vocabulary's
*Changes* table beside the counter, because the counter without the rule
answers nothing.

## Verdict

Two rows. One into the *Metrics* table of `vocabulary.md`, with a bare
instrument word, `none` when the backend derives it:

```
| <namespace.noun.measure> | <counter, updowncounter, histogram, gauge, or none> | <UCUM unit> | <labels from the label tier, or (none)> | <no, or "yes, derived: see backends/<backend>/screens.md"> |
```

And one into the *Changes* table, so the question survives. Never prose lines
after a table row; the checker reads the table and stops at the first line
that is not a row:

```
| <date> | <who> | <metric>: question "<sentence from step 1>", pattern <pattern name>, recorded <moment, e.g. at close, or callback each interval>, combine <sum|max|per process> |
```

An observable instrument is still `gauge` in the cell; name it on the
`observable instruments:` line under the table.

## Never

- Never answer a percentile question with an average.
- Never measure a thing that may never end only at its end.
- Never put an instance id on a metric to get per instance lines.
- Never compute a percentile inside a process and export the number.
- Never emit a metric the backend derives from an existing span.

## Stop and ask

- The question fits no pattern. Write the sentence from step 1 and ask.
- The registry of open things does not exist in the code, so the open gauge
  has nothing to walk. A person decides where the registry lives.
- The label the person wants to group by fails `metrics/labels.md`.

## Examples

| Question | Pattern | Measurement |
| --- | --- | --- |
| p95 of environment duration | Duration that may never end | histogram `sahara.environment.duration` in `s` at close with label `outcome` in `completed, abandoned`; observable gauges `sahara.environment.open.count` in `{environment}` and `sahara.environment.open.age.max` in `s` |
| How many entities exist right now | Level | up down counter `sahara.entities.live` in `{entity}` labelled by `sahara.entity.definition` |
| Tests per minute | Rate | derived from test root spans |
| Did the nightly cycle run | Absence | counter `sahara.cycle.completed` plus a no-data alert |
| Why was this test slow | none, a trace question | open the test's trace |
