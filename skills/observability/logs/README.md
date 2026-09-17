# Logs

Procedures and recipes for the `log` verdict from `core/signal-choice.md`.
Target: Python `logging` on opentelemetry-python 1.2x, shipped to Elastic
Stack 8.x either as JSON lines through Filebeat or Elastic Agent, or over
OTLP through APM Server.

## Files

| File | Answers |
| --- | --- |
| `log-or-span-event.md` | is this moment a log line at all, or a span event |
| `levels.md` | `ERROR`, `WARN`, `INFO` or `DEBUG`, and what to do with exceptions |
| `structure.md` | the message template, the ECS field names, JSON to stdout or a file |
| `trace-correlation.md` | how `trace.id`, `span.id` and the run level keys get onto every line |
| `recipes/python_logging_setup.py` | `configure_logging(...)` for JSON lines and `configure_logging_otlp(...)` for OTLP |

## Order for an Instrument task

1. Read `vocabulary.md` in the project. If the line is already in its *Logs*
   table, skip to step 5.
2. `log-or-span-event.md`. A `span event` verdict sends you to `traces/`.
3. `levels.md`, then `structure.md`. Write the template, level and fields into
   the vocabulary.
4. `trace-correlation.md` once per project, to pick the mechanism.
5. Copy `recipes/python_logging_setup.py` once per project. Call
   `configure_logging` or `configure_logging_otlp` at process start, after
   the tracing setup. Change only what the top comment names.
6. At the call site write `logger.info("cycle started", extra={...})` with
   the template string and fields from the vocabulary, nothing else.
7. Run once, compare a line with the bottom comment of the recipe, then run
   the logs checker in `checks/` on real output and paste its result.

Every UNVERIFIED line names a fact to confirm on the running installation.
