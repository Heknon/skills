# Which signal

**Verdict you produce:** one of `span`, `span event`, `metric`, `log`, or
`derived`. Then you load the folder the verdict names and nothing else.

Answer the questions in order. The first yes is the verdict.

## Questions

1. **Does it happen, with a start and an end you can put code around?**
   A function call, a request, a query, a phase.
   **Yes: `span`.** Load `traces/`.

2. **Is it a fact about one moment inside work that already has a span?**
   A retry happened, a cache missed, a threshold was crossed, a payload arrived.
   **Yes: `span event`.** Load `traces/span-attributes-and-events.md`.
   Not a log line: a log line inside a span is a second copy of the same fact
   that lives in a different index and can be sampled apart from its span.

3. **Is it a number you want to chart over time, with no unit of work around
   it, or too frequent to record each occurrence?**
   Queue depth, memory in use, items per second, connections open.
   **Yes: `metric`.** Load `metrics/`.

4. **Is it a message a person must be able to find later, even when the work
   around it was sampled away, or when there is no span at all?**
   Startup and shutdown, configuration loaded, a background failure with no
   request, an audit fact.
   **Yes: `log`.** Load `logs/`.

5. **Is it a count or a duration of something that already has a span?**
   Requests per minute, request latency, failure rate, time in a dependency.
   **Yes: `derived`.** The backend computes it from the spans. Emit nothing.
   Confirm in `metrics/derived-or-emitted.md` that this backend derives it.

## Verdict

Write into `vocabulary.md` under the signal's section, using the naming rules
from `core/naming-and-cardinality.md` for the name.

## Never

- Never emit two signals for one fact. A span plus a log line saying the span
  happened, or a span plus a histogram of its duration, is a duplicate the
  backend already made.
- Never turn a span into a log line because logging is easier to add. The
  span carries the parent, the duration and the outcome; the log line carries
  a string.
- Never turn a metric into a span because you want it on a trace. A gauge
  sampled every second inside a span is a span per second.

## Stop and ask

- It is both a thing that happens and a number to chart, and the backend does
  not derive metrics from spans. A person picks which one matters more, or
  approves emitting both with the metric marked as duplicate in the
  vocabulary.
- You cannot tell whether there is a span around it. Look at the vocabulary's
  unit of work. If the moment is inside the unit, there is a span around it.

## Examples

| Fact | Verdict | Why |
| --- | --- | --- |
| An entity was created | span | it starts, it ends, it can fail |
| Create retried once before succeeding | span event | a moment inside the create span |
| Worker heap size | metric | no unit around it, sampled |
| Test duration | derived | the test span already has it |
| Plugin loaded configuration file X | log | happens before any span exists |
| Revert restored tag T | span, with `tag` as an attribute | it starts and ends |
| Tests per minute across the cycle | derived | count of test root spans |
