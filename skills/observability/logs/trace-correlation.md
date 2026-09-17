# Trace correlation

**Verdict you produce:** which of the three mechanisms below this project
uses, and the exact field names each log line carries as a result. It goes
into the *Correlation keys* table of `vocabulary.md`, *Where* column.

A log line is correlated when the backend can walk from it to the trace and
back. That needs `trace.id` and `span.id` on the line, spelled that way, plus
the run level keys for lines written outside any span. Nobody types these at
a call site. Invariant 9.

## Questions

1. **Are lines shipped as files or stdout by a log shipper?** The shipper is
   whichever `backends/<backend>/collector.md` names for this installation.
   Yes: **mechanism A**, the logging filter. `configure_logging(...)` in
   `recipes/python_logging_setup.py`.
2. **Is the SDK already exporting spans over OTLP and nothing ships files?**
   Yes: **mechanism C**, the OTLP `LoggingHandler`.
   `configure_logging_otlp(...)` in the same recipe. Read the limits below.
3. **Is the process run under `opentelemetry-instrument` with no code of
   yours in the startup path?** Yes: **mechanism B**, `LoggingInstrumentor`,
   and your formatter must translate its field names.
4. **Are there lines outside any span?** Startup, worker assignment, cycle
   end. Always yes. Every mechanism also copies the run level correlation keys
   from the vocabulary module onto every record.

## Mechanism A: a `logging.Filter`

The filter reads `trace.get_current_span().get_span_context()`. When
`is_valid`, it sets `trace.id = format(context.trace_id, "032x")` and
`span.id = format(context.span_id, "016x")`. When not, it sets neither. It
also sets `sahara.cycle.id`, `sahara.environment.id` and `sahara.worker.id`
from the vocabulary module on every record, and copies `test.nodeid_hash`
from the current span when that span carries it. The JSON formatter writes
them as they are, in the OTel spelling; whatever the shipper or the backend
renames them to is its own doing, recorded in the *Backend spelling* column
from `backends/<backend>/mapping.md`.

## Mechanism B: `LoggingInstrumentor`

Package `opentelemetry-instrumentation-logging`.
`LoggingInstrumentor().instrument(set_logging_format=False)` replaces the log
record factory so every `LogRecord` carries:

| Attribute | Inside a span | Outside a span |
| --- | --- | --- |
| `otelTraceID` | 32 hex characters | the string `"0"` |
| `otelSpanID` | 16 hex characters | the string `"0"` |
| `otelTraceSampled` | `True` or `False` | `False` |
| `otelServiceName` | `service.name` from the tracer provider's resource | same, or `""` |

Under `opentelemetry-instrument` it is turned on by
`OTEL_PYTHON_LOG_CORRELATION=true`; `OTEL_PYTHON_LOG_FORMAT` and
`OTEL_PYTHON_LOG_LEVEL` change its `basicConfig` call. It writes nothing in
ECS spelling. The formatter must map `otelTraceID` to `trace.id` and
`otelSpanID` to `span.id`, and drop the `"0"`. The recipe's formatter does
that when the attributes are present, so A and B can coexist.

## Mechanism C: OTLP logs

`opentelemetry.sdk._logs.LoggerProvider(resource=...)`,
`opentelemetry._logs.set_logger_provider(provider)`,
`provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))`,
then `logging.getLogger().addHandler(LoggingHandler(level=logging.NOTSET, logger_provider=provider))`.
The module is still spelled `_logs` with an underscore in 1.2x. The exporter
is `opentelemetry.exporter.otlp.proto.http._log_exporter.OTLPLogExporter`,
default path `v1/logs`, environment `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` then
`OTEL_EXPORTER_OTLP_ENDPOINT`.

The handler takes `trace_id`, `span_id` and `trace_flags` from the current
span itself. It turns every non standard attribute of the record into an
OTLP attribute, so a filter that sets `record.__dict__["sahara.cycle.id"]`
ships it. It sets `code.file.path`, `code.function.name`,
`code.line.number`, and for `exc_info` the attributes `exception.type`,
`exception.message`, `exception.stacktrace`.

### On Elastic

What APM Server 8.x does with an OTLP log record, from `elastic/apm-data`
`input/otlp/logs.go`:

| OTLP | Elastic field |
| --- | --- |
| body | `message` |
| `severity_text` | `log.level`, so `WARN` not `WARNING` |
| `severity_number` | `event.severity` |
| trace id, span id | `trace.id`, `span.id` |
| attribute `sahara.cycle.id` | `labels.sahara_cycle_id`, dots to underscores, strings; numbers go to `numeric_labels.*` |
| `exception.type`, `exception.message`, `exception.stacktrace` | `error.exception.*`, and the record becomes an error document in `logs-apm.error-<namespace>` with `event.type: error` |
| everything else | `logs-apm.app.<service.name>-<namespace>` |

Limits in 8.x: Elastic marks OTLP logs intake "technical preview", and
states that the `app_logs` data stream "has dynamic mapping disabled", so a
field that is not `labels.*`, `numeric_labels.*` or a mapped ECS field is
stored but not searchable. Keep custom fields as record attributes, which
land under `labels.`.

## Other backends

Other backends: the verdicts do not change; the stored shape is in
backends/<backend>/mapping.md and the differences in backends/paradigms.md.

## Verdict

Rows of the *Correlation keys* table:

```
| trace.id, span.id | string | every log inside a span | <stored spelling per backends/<backend>/mapping.md> | mechanism A filter, from the current span |
| sahara.cycle.id | string | every span, every log | <stored spelling per backends/<backend>/mapping.md> | filter copies it from the vocabulary module |
| test.nodeid_hash | string | every span except session.run, every log inside a span | <stored spelling per backends/<backend>/mapping.md> | filter copies it from the current span |
```

## Never

- Never pass `trace_id` through `extra=` at a call site.
- Never write `"0"` into `trace.id`. Absent is correct outside a span.
- Never spell it `traceId`, `trace_id` or `otelTraceID` in a shipped line.
- Never write a backend spelling such as `labels.sahara_cycle_id` into a
  shipped line. The line carries `sahara.cycle.id`; the rename is the
  shipper's or the backend's, never the recipe's.
- Never ship the same line by mechanism A and mechanism C. Two documents.
- Never attach the OTLP handler to a logger the SDK itself logs through at
  `DEBUG`; the exporter's own logging then feeds the exporter.

## Stop and ask

- Lines are produced by a library with its own formatter you cannot replace.
- The sampler drops traces and the team wants every log line to still open
  a trace. That is a sampling decision.

## Examples

| Line | Where written | Fields it carries |
| --- | --- | --- |
| `entity create failed` at `debug` | inside `entity.create` | `trace.id`, `span.id`, `test.nodeid_hash`, `sahara.cycle.id`, `sahara.environment.id`, `sahara.worker.id` |
| `worker assigned environment` | outside any span | `sahara.cycle.id`, `sahara.environment.id`, `sahara.worker.id`, no `trace.id` |
| `configuration loaded` | before the SDK starts | `sahara.cycle.id` if known, nothing else |
