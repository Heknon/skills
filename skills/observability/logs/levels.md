# Log levels

**Verdict you produce:** one of `ERROR`, `WARN`, `INFO`, `DEBUG` for each
log line. It goes into the *Level* column of the *Logs* table in
`vocabulary.md`.

Four levels. Each one is a promise about who reads it. The Python constants
are `logging.ERROR`, `logging.WARNING`, `logging.INFO`, `logging.DEBUG`. The
value of `log.level` on the shipped line is `ERROR`, `WARN`, `INFO` or
`DEBUG`: the Python level name, except that `WARNING` is written `WARN`.
That is what the OTLP `LoggingHandler` ships, and the JSON formatter in the
recipe writes the same so both paths agree. `CRITICAL` is not used.

## The four levels

| Level | One sentence | Rule |
| --- | --- | --- |
| `ERROR` | Something is broken and someone must act. | A person is paged or opens a ticket for every line. If nobody would, it is not an error. |
| `WARN` | Something is off and someone should look. | A person reads it in the morning. It names a condition that will become an error if it repeats. |
| `INFO` | State changed. | Started, stopped, loaded, assigned, finished. One line per change, never per iteration. |
| `DEBUG` | Developers only. | Off in production. Anything you would delete before a code review goes here. |

## Questions

1. **Will a person act on this line within the hour?** Yes: `ERROR`.
2. **Will a person want to look at it later, without being told to?**
   Yes: `WARN`, which is `logger.warning(...)` in code.
3. **Did the process, the run or the environment change state?**
   Yes: `INFO`.
4. Otherwise `DEBUG`, or nothing.

## Exceptions

An exception inside a span is recorded on the span with
`span.record_exception(exception)` and `span.set_status(StatusCode.ERROR)`.
That is the copy that Kibana shows under Errors and counts in the failure
rate. A second copy at `ERROR` in the logs makes every failure two alerts.

- Inside a span: log it at `DEBUG` with `exc_info=True`, or not at all.
- Outside a span: log it at `ERROR` with `exc_info=True`. The formatter
  writes `error.type`, `error.message` and `error.stack_trace`.
- A caught exception that the code recovers from, inside a span: a span
  event, see `logs/log-or-span-event.md`. Outside a span: `WARN` without
  the traceback.

Observable check: at the `except`, is `trace.get_current_span().get_span_context().is_valid`
true? Then it is a span concern.

## Production setting

The level comes from the environment variable `LOG_LEVEL`, default `INFO`,
read once by `configure_logging` in `recipes/python_logging_setup.py`. A
developer sets `LOG_LEVEL=DEBUG` locally. CI and production never do.

## Verdict

```
| worker assigned environment | INFO | labels.cycle_id, labels.environment_id, labels.worker_id | yes |
```

## Never

- Never log at `ERROR` from inside a span. The span carries the error.
- Never log inside a loop at `INFO`. Once per state change.
- Never use `CRITICAL`, `FATAL`, `NOTICE`, `TRACE` or a custom level.
- Never log at `WARN` something that happens on every run. It is `INFO`
  or it is noise.
- Never leave `DEBUG` on in CI to "have more data". Turn on tracing instead.
- Never write the level into the message.

## Stop and ask

- Two readers disagree on whether someone acts on the line.
- A line is wanted at `ERROR` that fires more than a few times per cycle.
  That is a metric or a span status, and a person decides which.

## Examples

| Line | Level | Why |
| --- | --- | --- |
| `configuration load failed`, process cannot start | `ERROR` | someone fixes it now, no span yet |
| `controller unreachable, retrying`, outside any test | `WARN` | look in the morning; becomes an error if it persists |
| `cycle started`, `cycle finished`, `worker assigned environment` | `INFO` | state changed, once each |
| `poll response body`, the JSON | `DEBUG` | developers, off in production |
| assertion error inside a test | none | `record_exception` on the test span |
| entity create timed out inside a test | none | status `ERROR` on the `entity.create` span |
| environment revert skipped because tag missing | `WARN` if outside a span, span event if inside | somebody should look |
