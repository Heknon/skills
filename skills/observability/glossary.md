# Glossary

One sentence per term. The OpenTelemetry name first, the Elastic name beside
it where Elastic uses a different word. Use these words and no synonyms.

## Traces

| OpenTelemetry | Elastic | Meaning |
| --- | --- | --- |
| trace | trace | Every span that shares one `trace_id`; one occurrence of a unit of work and everything it caused. |
| span | transaction or span | One timed operation with a name, a kind, a status, attributes, events and links. |
| root span | transaction | A span with no parent; the unit of work. Elastic also calls a span with a remote parent a transaction. |
| child span | span | A span whose parent is in the same process. |
| span kind | transaction.type / span.type derivation | `INTERNAL`, `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`; says which side of a call the span is. |
| exit span | exit span | A `CLIENT` or `PRODUCER` span; the thing it called becomes a dependency. |
| parent | parent | The span active in the code when this one started; exactly one or none. |
| link | span.links | A reference to another span this one belongs to or was caused by; any number; never followed by aggregation. |
| span context | trace.id, span.id, sampled flag | The four values that identify a span and travel with it across boundaries. |
| attribute | label | A key and a typed value on a span, metric point or log record. Elastic stores non-ECS ones under `labels.*`. |
| resource attribute | service.*, host.*, process.* | An attribute describing the process, set once at startup and inherited by every signal. |
| event | span event | A named, timestamped fact inside a span, with its own attributes. |
| exception event | error document | The event named `exception` that `record_exception` writes; Elastic also indexes it as an error. |
| status | event.outcome | `UNSET`, `OK` or `ERROR` with a description; Elastic maps `ERROR` to `failure`. |
| propagation | distributed tracing | Carrying the span context across a thread, process or network boundary so the trace continues. |
| propagator | | The code that writes span context into headers or an environment variable and reads it back. W3C `traceparent` by default. |
| sampler | sampling | The decision, made at the root, whether a trace is recorded and exported. |
| tail sampling | tail-based sampling | Deciding after the trace is complete, in a collector or in APM Server, instead of at the root. |
| span processor | | Code that sees every span at start and end; used to stamp correlation keys and to batch for export. |
| exporter | | Code that sends finished spans somewhere: OTLP to a collector or APM Server, the console, a file. |

## Metrics

| OpenTelemetry | Elastic | Meaning |
| --- | --- | --- |
| instrument | | The object you record into: counter, up down counter, histogram, gauge. |
| counter | | A sum that only goes up; ask it for rates. |
| up down counter | | A sum that goes up and down; a current total such as in-flight requests. |
| histogram | histogram field | A distribution of values; ask it for percentiles. |
| gauge | | A current level sampled at a moment; memory in use, queue depth. |
| observable instrument | | An instrument that pulls its value from a callback at export time instead of being recorded into. |
| data point | metrics document | One exported value or bucket set with its attributes and timestamp. |
| label | dimension | A metric attribute the backend groups by; every distinct combination is a time series. |
| time series | | One metric with one combination of label values over time. |
| unit | unit | The UCUM string on the instrument, such as `s`, `By`, `1`, `{request}`. |
| view | | SDK configuration that renames an instrument, drops attributes or sets histogram buckets. |
| derived metric | span metrics, service destination metrics | A metric the backend computes from spans; not emitted by the SDK. |
| exemplar | | A trace id attached to a metric data point so a chart can open a trace. |

## Logs

| OpenTelemetry | Elastic | Meaning |
| --- | --- | --- |
| log record | log document | One line: timestamp, severity, body, attributes, and the span context if inside a span. |
| body | message | The text of the line; a fixed template, with values in fields. |
| severity | log.level | Shipped as `ERROR`, `WARN`, `INFO`, `DEBUG`; written in the vocabulary's *Level* column as `error, warn, info, debug`; how the backend stores the word is in `backends/<backend>/mapping.md`. |
| message template | | The fixed sentence a line is grouped by; never contains a value. |
| field | field | A key and value beside the message; ECS names where they exist. |
| trace correlation | trace.id, span.id on the line | The log record carrying the span context of the span it was written inside. |

## Pipeline

| Term | Meaning |
| --- | --- |
| SDK | The OpenTelemetry library inside the process; makes spans, metrics and log records and exports them. |
| OTLP | The wire protocol the SDK speaks, over gRPC or HTTP; what the collector and APM Server receive. |
| collector | The OpenTelemetry Collector, a separate process that receives, processes and forwards telemetry. |
| processor | A collector stage that changes data in flight: batch, memory limit, add or delete attributes, sample. |
| connector | A collector stage that turns one signal into another, such as spans into metrics. |
| APM Server | Elastic's receiver; turns OTLP into Elastic documents, renames fields, aggregates span metrics. |
| Elastic Agent | The process that runs APM Server as an integration when managed by Fleet. |
| Fleet | The Kibana app where an Elastic Agent's integrations and their settings live. |
| data stream | Where Elastic stores documents; `traces-apm-*`, `metrics-apm.*`, `logs-apm.*`. |
| ECS | Elastic Common Schema; the field names Elastic maps known attributes onto. |
| mapping | The type Elasticsearch fixed for a field the first time it saw one; cannot change without reindexing. |
| cardinality | The number of distinct values a field takes over the life of the index. |
| APM app | The Kibana application with Services, Transactions, Dependencies, Errors and Service map. |

## This skill

| Term | Meaning |
| --- | --- |
| unit of work | The thing that becomes a root span and that every screen aggregates over. |
| instance key | The attribute that identifies one occurrence of the unit. |
| correlation key | An attribute carried by every signal so they can be joined. |
| tier | Whether a value is a name, a label or an attribute; decides where it may appear. |
| vocabulary | The project's `vocabulary.md`; the only source of names once it exists. |
| verdict | The one line a procedure produces and you write into the vocabulary. |
| stop and ask | Writing down what is missing and asking a person instead of inventing. |
| checker | A script in `checks/` that judges an export against the vocabulary. |
| rung | One hop in the verification ladder with a command and an expected output. |

## The same thing in each stack

| Concept | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| root span | transaction | trace root in Tempo | trace root in VictoriaTraces |
| span attribute | `labels.*` or `numeric_labels.*` | `span.*` in TraceQL | span tag through the Jaeger API |
| resource attribute | `service.*`, `host.*`, `labels.*` | `resource.*` in TraceQL; `target_info` and `job`/`instance` in Prometheus | `target_info` and labels in VictoriaMetrics |
| metric label | dimension on a metrics document | Prometheus label, dots to underscores | VictoriaMetrics label |
| log field | ECS field | stream label or structured metadata in Loki | field in VictoriaLogs |
| span metrics | APM Server | Tempo metrics-generator or the collector's `span_metrics` connector | the collector's `span_metrics` connector |
| dependency view | Dependencies tab and service map | service graph from the `service_graph` connector or metrics-generator | node graph over `service_graph` series, if any |
| metric to trace | not through exemplars | exemplars in Prometheus, opened in Tempo | exemplars are limited; use the trace id label or time range |
| trace to logs | `trace.id` on the log document | derived field or `trace_id` structured metadata in Loki | `trace_id` field in VictoriaLogs |
| trace query | KQL over `traces-apm*` | TraceQL | Jaeger API search or LogsQL over the trace store |

The span metrics and dependency view rows are a summary. Who derives span
metrics and the service graph, what must be enabled and what it is called is
the table in `backends/paradigms.md`; that table wins.
