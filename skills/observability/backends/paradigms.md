# Paradigms: the same question on each stack

Three stacks, one question per row, three answers. Every answer is a pointer
into the folder that verified it. Read this once before any Query, Debug or
Choose task, and again whenever an answer from one stack is about to be used
on another. `choosing.md` is the procedure that turns these differences into
a decision.

The three are not three spellings of one thing. Elastic is **one store that
does everything and derives the APM screens itself**. The Grafana stack is
**one store per signal, and a component you enable derives the screens**. The
Victoria stack is **one store per signal built for volume, and only the
collector derives anything**. Most mistakes come from carrying an assumption
across that line.

## Where span metrics and dependencies come from

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Who computes RED per unit of work | APM Server, from every span, always | Tempo's metrics-generator, or the collector's `span_metrics` connector; you enable one | the collector's `span_metrics` connector writing into VictoriaMetrics; nothing else |
| Who computes what a service calls | APM Server, from exit spans, always | metrics-generator `service-graphs`, or the collector's `service_graph` connector | the collector's `service_graph` connector; VictoriaTraces has an experimental dependencies task |
| Where the numbers land | `metrics-apm.transaction.*`, `metrics-apm.service_destination.*` | Prometheus series `traces_spanmetrics_*` or `traces_span_metrics_*`, `traces_service_graph_*` | VictoriaMetrics series with the same names |
| What is on by default | everything | nothing | nothing |
| The double counting trap | emit no latency histogram of a spanned thing | generator and connector both on | connector twice, once per pipeline |
| Where it is written | `elastic/overview.md`, `metrics/derived-or-emitted.md` | `grafana/overview.md`, `grafana/collector.md` | `victoria/overview.md`, `victoria/collector.md` |

Consequence for the verdicts: on Elastic the answer to "should I emit request
latency" is always `derived`. On the other two it is `derived` only after
someone enabled the component, and `stop and ask` before that.

## What a root span becomes

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Name for it | transaction; also any `SERVER` or `CONSUMER` span with a remote parent | nothing special; a span with no parent, found by `trace:rootName` | nothing special; empty `parent_span_id` |
| Does its kind matter for the screens | no; a root of any kind is a transaction | yes; Grafana's span metrics table filters `span_kind="SPAN_KIND_SERVER"` by default, so an `INTERNAL` root is in the series but not in that table | only through the connector's `span.kind` dimension |
| Where it is written | `elastic/overview.md` | `grafana/screens.md`, the span metrics table row | `victoria/mapping.md` |

Consequence: a test harness whose roots are `INTERNAL` gets a transactions
table on Elastic for free, and on Grafana gets series it must chart itself or
a root kind it must change with a person's agreement.

## What happens to an attribute key

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| On a span | non-ECS keys go under `labels.*`, dots to underscores; numbers under `numeric_labels.*` | Tempo keeps the key as sent; query it as `span."sahara.cycle.id"` | VictoriaTraces keeps it under `span_attr:` prefixes |
| On a metric | a field on the metrics document | Prometheus rewrites to `sahara_cycle_id`, appends the unit and `_total` per `translation_strategy` | kept as sent by default; `-opentelemetry.usePrometheusNaming` switches to the Prometheus spelling |
| On a log line | ECS field or `labels.*` | Loki: a few keys become stream labels with dots to underscores, the rest structured metadata | VictoriaLogs keeps the key; resource attributes become stream fields |
| Type mixing | splits into `labels.*` and `numeric_labels.*` silently | Prometheus labels are strings; Tempo keeps the type per span | labels are strings; VictoriaLogs stringifies |
| Where it is written | `elastic/mapping.md` | `grafana/mapping.md` | `victoria/mapping.md` |

Consequence: the vocabulary's *Backend spelling* column has three different
answers for the same key, and a query copied between stacks is wrong on
arrival.

## Going from one signal to another

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Metric to trace | not through exemplars; by time range and labels | exemplars: Prometheus keeps `trace_id`, Grafana opens it in Tempo, needs `--enable-feature=exemplar-storage` | exemplars are dropped on ingest; by time range and labels |
| Trace to logs | `trace.id` on the log document, the Logs tab | Loki `trace_id` structured metadata, a derived field or the Tempo data source's trace to logs | VictoriaLogs `trace_id` field, a custom query in the data source |
| Logs to trace | click `trace.id` | derived field in the Loki data source | derived field in the VictoriaLogs data source |
| Where it is written | `elastic/screens.md` | `grafana/screens.md` | `victoria/screens.md` |

## Query languages

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Traces | KQL over `traces-apm*`, Elasticsearch DSL for aggregations | TraceQL | Jaeger API search, LogsQL over the trace store |
| Metrics | Lens and KQL over `metrics-apm*` | PromQL | MetricsQL, a superset of PromQL with differences in `rate` |
| Logs | KQL, Discover | LogQL | LogsQL |
| Files | `elastic/queries.md`, `elastic/queries-dsl.md` | `grafana/queries.md`, `grafana/queries-promql.md` | `victoria/queries.md` |

## Sampling and what it does to the numbers

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Head sampling and derived counts | weighted by `transaction.representative_count`, which the Python SDK does not set, so counts come out low | the generator counts what reached Tempo; the connector counts what the collector saw; place the connector before any sampler | the connector counts what the collector saw |
| Tail sampling lives in | APM Server or the collector | the collector's `tail_sampling`, whole traces on one collector | the collector |
| Where it is written | `core/sampling-and-volume.md`, `elastic/overview.md` | `grafana/overview.md`, `grafana/collector.md` | `victoria/collector.md` |

## Operating shape

| | Elastic | Grafana stack | Victoria stack |
| --- | --- | --- | --- |
| Processes to run | Elasticsearch, Kibana, APM Server under Elastic Agent | Tempo, Loki, Prometheus or Mimir, Grafana, usually a collector | VictoriaMetrics, VictoriaLogs, VictoriaTraces, Grafana, a collector for span metrics |
| Storage | Elasticsearch indices and data streams | object storage for Tempo and Loki, local disk for Prometheus | local disk, single binaries |
| Full text search over logs | yes, it is an index | no, labels then grep | no, fields then grep |
| Cardinality pressure shows up as | field mapping limits, `_ignored` | series count, memory in Prometheus | series count, `vmui` cardinality explorer |
| Trace store maturity | mature | mature | VictoriaTraces is pre GA at the stamp date; read `victoria/overview.md` |
| Where it is written | `elastic/overview.md`, `elastic/elastic-agent.md` | `grafana/overview.md` | `victoria/overview.md` |

## What does not change

- The procedures in `core/`, `traces/`, `metrics/` and `logs/`. The unit of
  work, the correlation keys, the tiers, the error rules and the signal
  choice are the same on all three.
- The SDK code. One `configure_tracing`, one exporter endpoint, and the
  stack behind it is a deployment detail.
- The checkers. They read the export before any backend touches it.
- The vocabulary's names. Only its *Backend spelling* column changes.

## Never

- Never use a field name, a series name or a screen name from one column in
  another column's stack.
- Never assume span metrics exist. On two of the three stacks they exist only
  after someone turned them on.
- Never assume a metric can open a trace. Only the Grafana stack does that
  through exemplars, and only with the feature flag.
- Never copy a query between stacks. Same question, new query, from that
  stack's `queries.md`.

## Stop and ask

- The installation mixes columns, such as Tempo for traces and Elastic for
  logs. Legitimate, but the join across products needs a person to confirm
  the data source links.
- A row above says "pre GA" or "experimental" for the component you are
  about to rely on.
