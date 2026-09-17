# Elastic APM: the path from SDK to screen

verified against: Elastic Observability guide 8.17, Elasticsearch 8.17 index
templates, elastic/apm-data `input/otlp` source read 2026-09-17. Facts taken
from source rather than a guide page are marked `source:`.

## The hops

```
OpenTelemetry SDK --OTLP--> [Collector, optional] --OTLP--> APM Server
   under Elastic Agent, port 8200, gRPC and HTTP on the same port
   --> Elasticsearch data streams --> Kibana APM app
```

1. **SDK.** Exports spans, metrics and logs over OTLP. An unsampled span is
   never exported, so the backend never sees it.
2. **Collector.** Optional. Forwards with the `otlp` or `otlphttp` exporter
   to APM Server. See `collector.md`. Do not point the Collector's
   `elasticsearch` exporter at the APM data streams. The 8.17 limitations
   page says that exporter is not intended for use with Elastic APM.
3. **APM Server.** Listens on `:8200`. Accepts OTLP/gRPC and OTLP/HTTP,
   protobuf only. JSON encoding for OTLP/HTTP is not supported in 8.17.
   Auth header: `Authorization=Bearer <secret_token>` or
   `Authorization=ApiKey <api_key>`, with the space. APM Server translates
   OTLP into APM documents, computes aggregated metrics, and indexes.
   OTLP metrics must arrive with **delta** temporality: set
   `configure_metrics(..., temporality="delta")` from
   `metrics/recipes/python_meter_setup.py`, whose default `cumulative` is for
   Prometheus, Mimir and VictoriaMetrics, and write
   `metric temporality: delta` into the installation block of
   `backends/README.md`.
4. **Elasticsearch.** Data streams named `<type>-<dataset>-<namespace>`.
   The namespace is set in the APM integration policy, default `default`.
5. **Kibana APM app.** Reads the index patterns in its settings:
   `xpack.apm.indices.transaction` and `xpack.apm.indices.span` default to
   `traces-apm*,apm-*,traces-*.otel-*`, `xpack.apm.indices.error` to
   `logs-apm*,apm-*,traces-*.otel-*`, `xpack.apm.indices.metric` to
   `metrics-apm*,apm-*,metrics-*.otel-*`.

## Where each signal lands

| Data stream | Holds | Written by |
| --- | --- | --- |
| `traces-apm-<namespace>` | transaction and span documents, told apart by `processor.event` = `transaction` or `span` | APM Server, per OTLP span |
| `traces-apm.sampled-<namespace>` | tail-based sampling working data. UNVERIFIED: exact document shape. Never query it for answers | APM Server, only with tail-based sampling on |
| `traces-apm.rum-<namespace>` | RUM and iOS agent traces. Not on this path | RUM agents |
| `logs-apm.error-<namespace>` | error documents, one per `exception` span event and per OTLP log record carrying `exception.*` attributes | APM Server |
| `logs-apm.app.<service.name>-<namespace>` | OTLP log records, and span events whose name is not `exception`. Dynamic mapping is disabled on this stream in 8.x, issue 9093 | APM Server |
| `metrics-apm.app.<service.name>-<namespace>` | OTLP metrics you emit | APM Server |
| `metrics-apm.internal-<namespace>` | `span_breakdown` metricsets and other server internal metrics | APM Server |
| `metrics-apm.transaction.<interval>-<namespace>` | `metricset.name: transaction`, one series per `transaction.name`, `transaction.type`, `transaction.result`, `event.outcome`, service and host dimensions, plus `labels` and `numeric_labels` | APM Server aggregation |
| `metrics-apm.service_transaction.<interval>-<namespace>` | `metricset.name: service_transaction`, per `service.name`, `service.environment`, `transaction.type` | APM Server aggregation |
| `metrics-apm.service_destination.<interval>-<namespace>` | `metricset.name: service_destination`, per `service.name`, `span.destination.service.resource`, `service.target.type`, `service.target.name`, `span.name`, `event.outcome` | APM Server aggregation |
| `metrics-apm.service_summary.<interval>-<namespace>` | `metricset.name: service_summary`, per `service.name`, `service.environment` | APM Server aggregation |

`<interval>` is `1m`, `10m` or `60m`. All three are produced since 8.7 and the
aggregation streams are hidden. In the `<service.name>` position the name is
lowercased and `\ / * ? " < > | space , # : -` become `_`. source:
`model/modelprocessor/datastream.go`.

## The four document kinds

| Document | `processor.event` | Key fields | One per |
| --- | --- | --- | --- |
| transaction | `transaction` | `transaction.id`, `transaction.name`, `transaction.type`, `transaction.result`, `transaction.duration.us`, `transaction.sampled`, `event.outcome`, `trace.id`, `parent.id` | OTLP span that is a root, or has kind `SERVER` or `CONSUMER` |
| span | `span` | `span.id`, `span.name`, `span.type`, `span.subtype`, `span.action`, `span.duration.us`, `span.destination.service.resource`, `service.target.type`, `service.target.name`, `span.links`, `event.outcome`, `trace.id`, `transaction.id`, `parent.id` | every other OTLP span |
| error | `error` | `error.id`, `error.grouping_key`, `error.grouping_name`, `error.exception.type`, `error.exception.message`, `error.exception.stacktrace`, `error.exception.handled`, `error.culprit`, `trace.id`, `transaction.id`, `parent.id` | `exception` span event |
| metricset | `metric` | `metricset.name`, `metricset.interval`, `_doc_count`, `transaction.duration.histogram`, `transaction.duration.summary`, `span.destination.service.response_time.count`, `span.destination.service.response_time.sum.us`, `event.success_count` | aggregation bucket per interval |

Every kind also carries `service.name`, `service.environment`,
`service.version`, `agent.name`, `host.name`, `labels.*` and
`numeric_labels.*`. Resource attributes are copied onto every document.

## How an OTLP span becomes a transaction or a span

source: `input/otlp/traces.go`.

```
root := otelSpan.ParentSpanID().IsEmpty()
if root || kind == SERVER || kind == CONSUMER {
    transaction
} else {
    span
}
```

So the test root span becomes a transaction because it has no parent. The
session root becomes a transaction too, one per run. An entity operation with
kind `CLIENT` and a parent becomes a span.

After that decision:

- `transaction.name` and `span.name` are the OTLP span name, unchanged.
- `transaction.type` is `messaging` when messaging attributes are present,
  `request` when HTTP or RPC attributes are present, otherwise `unknown`.
  UNVERIFIED: no OTLP attribute is known to set `transaction.type` directly.
  Expect `unknown` for a test transaction, and select `unknown` in Kibana's
  transaction type selector.
- `transaction.sampled` is always `true`, because the SDK never exported the
  unsampled ones. `transaction.representative_count` comes from the W3C
  `tracestate` member `ot=p:<n>` as `2^n`, else `1`. Aggregated metrics are
  scaled by it.
- `event.outcome` comes from the span status: `OK` gives `success`, `ERROR`
  gives `failure`, `UNSET` gives `unknown`. When an HTTP status code is
  present it decides instead: a transaction is `failure` from 500, a span
  from 400.
- `exception` span events become error documents. Any other span event
  becomes a log document in `logs-apm.app.<service.name>-<namespace>` with
  `event.kind: event`, `message` = the event name, `trace.id`,
  `transaction.id`, `span.id` of the enclosing span, and the event's
  attributes under `labels.*` and `numeric_labels.*`. The span document
  itself keeps nothing of the event.
- Span links become `span.links`, each with `trace.id` and `span.id`. A link
  carrying the attribute `elastic.is_child: true` or `is_child: true` is
  stored as a child id instead of a link.

## What the aggregated metrics are made from

APM Server aggregates the documents it received. With head-based sampling the
metrics are calculated from the sampled events, scaled by
`transaction.representative_count`. With the Collector's `tailsamplingprocessor`
the sample rate is not propagated and the 8.17 limitations page says derived
throughput and count metrics are likely to be inaccurate. Use Elastic Agent
tail-based sampling instead if you must tail sample. Errors are kept
regardless of the sampling decision.

The `service_destination` metrics exist only for spans that carry
`span.destination.service.resource`. Everything the Dependencies screen shows
is a query over those metrics. See `screens.md`.

## How to read the running version

One row per component. Compare with the stamp at the top of the file you
are about to use; a different major is a stop and ask.

| Component | Command or place | Field to read |
| --- | --- | --- |
| Elasticsearch | `GET /` against the Elasticsearch URL | `version.number` |
| Kibana | `GET /api/status` against the Kibana URL | `version.number` |
| APM Server, standalone | `apm-server version` | the printed version |
| APM Server, under Elastic Agent | `elastic-agent version`, and Kibana **Integrations > Installed integrations > Elastic APM > Settings** | the agent version and the integration version |

## Never

- Never send the same span twice through two paths. Two APM Servers writing
  the same namespace double every metric.
- Never rely on an OTLP span event to appear in the trace waterfall. It is a
  separate log document.
- Never point the Collector's `elasticsearch` exporter at `traces-apm-*`.

## Stop and ask

- The installation runs 9.x and the traces are in `traces-*.otel-*`. That is
  OTel-native mode and the field names in this folder do not apply.
- A transaction type other than `unknown` is required by a person and the
  root span has no HTTP, RPC or messaging attributes.
