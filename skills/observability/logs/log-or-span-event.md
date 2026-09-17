# Log line or span event

**Verdict you produce:** `span event` or `log`. A span event goes into the
*Span events* table of `vocabulary.md`; a log into the *Logs* table.

Both record a moment. A span event lives on the span, shares its sampling
decision, its trace and its attributes, and costs nothing extra to
correlate. A log line is a document of its own that exists whether or not the
span does. One fact gets one of them. Invariant 8.

## Questions

1. **Is there a current span at this line of code?** Observe it:
   `trace.get_current_span().get_span_context().is_valid`. Print it once
   while running the code, or reason from the vocabulary: inside the unit
   of work there is always a span.
   **No: `log`.** Nothing to attach to.
2. **Must a person find this moment when the trace was sampled away?**
   Look at the sampler in the tracing setup. `ParentBased(ALWAYS_ON)` or a
   ratio of 1.0 means nothing is sampled away and the answer is no. Below
   1.0, ask: startup, shutdown, configuration, an audit fact, a safety
   interlock. **Yes: `log`.**
3. **Must a person find it without any trace, across all cycles, by its
   words?** For example a security team searching logs for one sentence with
   no APM access. **Yes: `log`.**
4. **Is it the exception that ends this span?** **Neither.** It is
   `span.record_exception` plus status `ERROR`, from
   `core/errors-and-status.md`. Not a log line.
5. Otherwise: **`span event`**. `span.add_event(name, attributes)` with the
   name from the vocabulary.

## What Elastic 8.x does with each

Source: `elastic/apm-data` `input/otlp/traces.go` and `logs.go`.

- A span event that is not named `exception` becomes a document with
  `event.kind: event`, `message` set to the event name, its attributes as
  `labels.*`, and `trace.id`, `span.id` and `transaction.id` filled in. It is
  routed to `logs-apm.app.<service.name>-<namespace>`, so it is searchable in
  Discover, but it has no `log.level` and it is dropped together with its
  span when the span is sampled away.
- A span event named `exception` with `exception.type` or `exception.message`
  becomes an error document in `logs-apm.error-<namespace>`.
- A log line shipped by Filebeat lands in `logs-<dataset>-<namespace>` under
  the dataset the integration was given, with whatever fields the line
  carries and no link to a span unless the line carries `trace.id`.
- A log line sent over OTLP lands in `logs-apm.app.<service.name>-<namespace>`
  with `trace.id` and `span.id` set when the record was made inside a span.

So the two are searchable alike. The difference is sampling, the level, and
who owns the moment: a span event belongs to a span; a log line belongs to a
process.

## Verdict

Span event:

```
| retry | entity.create, entity.call | attempt, wait_seconds |
```

Log:

```
| configuration loaded | INFO | file.path, labels.cycle_id | yes |
```

## Never

- Never log a moment that is inside a span at `INFO` or above. If it must be
  a log line, it passed question 2 or 3 and the vocabulary says why.
- Never add a span event and a log line for the same moment.
- Never log an exception that `record_exception` already recorded, except at
  `DEBUG`. See `logs/levels.md`.
- Never use a span event for something with a duration. That is a child
  span.
- Never put a value that changes per occurrence in the event name. The name
  is fixed; `attempt` is an attribute.

## Stop and ask

- The code runs both inside and outside spans, for example a helper called
  from a fixture and from a startup hook. Write the log verdict and ask
  whether the in span call should also carry a span event.
- The sampling rate is not written anywhere you can find.

## Examples

| Moment | Verdict | Why |
| --- | --- | --- |
| Create retried, attempt 2 | span event `retry` | inside `entity.create`, nobody needs it without the trace |
| Plugin read `sahara.toml` | log | before any span exists |
| Worker `gw3` was assigned environment `env-3` | log | outside the test unit; needed for every cycle |
| Controller returned a warning field | span event `controller.warning` | inside `entity.call` |
| Cycle interrupted by signal | log, `WARN` | must exist even when the last test's trace was sampled away |
| Test assertion failed | neither | status `ERROR` and `record_exception` on the test span |
| Revert restored tag `T` | span with `tag` attribute | it has a duration, see `core/signal-choice.md` |
