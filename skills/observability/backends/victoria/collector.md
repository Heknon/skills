# OpenTelemetry Collector between the SDK and the Victoria stack

Stamp: opentelemetry-collector-contrib component READMEs at `main`
(`otlphttpexporter`, `spanmetricsconnector`, `servicegraphconnector`,
`deltatocumulativeprocessor`), VictoriaMetrics v1.152.0, VictoriaLogs
v1.52.0 and VictoriaTraces v0.11.1 collector pages, read 2026-09-17.

**Verdict you produce:** either `no collector` or the path of the collector's
`config.yaml`, plus one line per processor that touches attributes and one
line per connector, copied into the vocabulary. Write it under *Correlation
keys* as `collector: <path or none>` and under *Metrics* as
`derived by: span_metrics, service_graph` for every row those connectors
cover.

## What the collector changes and what it does not

- It does **not** rename keys. `sahara.cycle.id` leaves it as
  `sahara.cycle.id`. The stores decide the spelling; `mapping.md`.
- It **does** compute the only RED and dependency metrics this stack will
  ever have, in the two connectors below. Remove them and every latency
  chart and the Service Graph go blank.
- It **does** convert delta to cumulative when `delta_to_cumulative` is in
  the metrics pipeline. VictoriaMetrics stores delta as is since v1.132.0
  and its docs still recommend converting.
- It **does** re-batch, drop under `memory_limiter`, and hold traces for
  `decision_wait` under `tail_sampling`, exactly as on Elastic.

Component names: `otlp_http` was `otlphttp`, `span_metrics` was
`spanmetrics`, `service_graph` was `servicegraph`, `delta_to_cumulative` was
`deltatocumulative`. The old names are deprecated aliases in current
contrib; an older binary knows only the old names and
`otelcol-contrib validate` says so. Keep one spelling per file.

## Known-good `config.yaml`

SDK sends OTLP to `localhost:4317` or `localhost:4318`. Rename the
`${env:...}` values and nothing else. VictoriaMetrics must run with
`-opentelemetry.usePrometheusNaming` for the names in the comments.

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  memory_limiter:                           # first processor in every pipeline
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128
  resource:
    attributes:
      - key: deployment.environment         # a label on every metric, a stream field on logs
        value: ${env:DEPLOYMENT_ENVIRONMENT}
        action: insert
  attributes/scrub:
    actions:
      - key: db.statement
        action: delete
  delta_to_cumulative:                      # metrics only; no effect on cumulative input
    max_stale: 5m
  batch:
    timeout: 1s
    send_batch_size: 512

connectors:
  span_metrics:                             # RED per service.name, span.name, span.kind, status.code
    namespace: traces.span.metrics          # default; becomes traces_span_metrics_ in VictoriaMetrics
    histogram:
      unit: ms                              # default; duration becomes traces_span_metrics_duration_milliseconds_bucket
      explicit:
        buckets: [10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2s, 5s, 10s, 30s, 60s]
    dimensions:                             # label tier only; never an id
      - name: sahara.entity.definition
    exclude_dimensions: ['collector.instance.id']   # one collector; the UUID label is noise
    aggregation_temporality: AGGREGATION_TEMPORALITY_CUMULATIVE
    metrics_flush_interval: 15s
    exemplars:
      enabled: false                        # VictoriaMetrics drops exemplars; see mapping.md
  service_graph:                            # edges client -> server
    latency_histogram_buckets: [100ms, 250ms, 1s, 5s, 10s]
    store:
      ttl: 10s                              # both spans of a pair must arrive within this
      max_items: 10000
    virtual_node_peer_attributes: [peer.service, db.name, db.system]   # default list; an entity definition becomes a server node
    metrics_flush_interval: 60s

exporters:
  otlp_http/victoriametrics:
    metrics_endpoint: http://${env:VICTORIAMETRICS_ADDR}/opentelemetry/v1/metrics   # cluster: http://<vminsert>:8480/insert/0/opentelemetry/v1/metrics
    encoding: proto                         # the only encoding the stores accept
    compression: gzip
    tls:
      insecure: true
  otlp_http/victorialogs:
    logs_endpoint: http://${env:VICTORIALOGS_ADDR}/insert/opentelemetry/v1/logs
    encoding: proto
    headers:
      VL-Stream-Fields: service.name,deployment.environment    # bounded resource keys only
      # AccountID: "0"                      # tenant, when not 0
    tls:
      insecure: true
  otlp_http/victoriatraces:
    traces_endpoint: http://${env:VICTORIATRACES_ADDR}/insert/opentelemetry/v1/traces
    encoding: proto
    headers:
      VT-Extra-Fields: collector=otelcol    # optional constant field on every span
    tls:
      insecure: true
  debug:                                    # verification ladder rung 2; remove in production
    verbosity: detailed
    sampling_initial: 5
    sampling_thereafter: 1

service:
  telemetry:
    logs:
      level: info
    metrics:
      readers:
        - pull:
            exporter:
              prometheus:
                host: '0.0.0.0'
                port: 8888                  # otelcol_exporter_sent_spans and friends
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlp_http/victoriatraces, span_metrics, service_graph, debug]
    metrics:
      receivers: [otlp, span_metrics, service_graph]
      processors: [memory_limiter, resource, delta_to_cumulative, batch]
      exporters: [otlp_http/victoriametrics, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes/scrub, batch]
      exporters: [otlp_http/victorialogs, debug]
```

Environment the collector reads: `DEPLOYMENT_ENVIRONMENT`,
`VICTORIAMETRICS_ADDR` such as `victoriametrics:8428`,
`VICTORIALOGS_ADDR` such as `victorialogs:9428`, `VICTORIATRACES_ADDR` such
as `victoria-traces:10428`. For OTLP/gRPC into VictoriaTraces use the `otlp`
exporter with `endpoint: <victoria-traces>:4317` and start VictoriaTraces
with `-otlpGRPCListenAddr=:4317`.

## What the connectors write

`span_metrics` emits, per `service.name`, `span.name`, `span.kind`,
`status.code` and each configured dimension:

- `traces.span.metrics.calls`, a cumulative counter of spans,
- `traces.span.metrics.duration`, an explicit histogram in `ms`,
- `traces.span.metrics.events` when `events.enabled`.

After `-opentelemetry.usePrometheusNaming`: `traces_span_metrics_calls_total`
and `traces_span_metrics_duration_milliseconds_bucket`, `_sum`, `_count`,
labels `service_name`, `span_name`, `span_kind`, `status_code`. The README
prints the values two ways, `span.kind="SERVER"` with `status.code="Ok"` in
its examples and `span_kind="SPAN_KIND_SERVER"` with
`status_code="STATUS_CODE_UNSET"` in an output sample. UNVERIFIED which one
your build emits: read
`curl 'http://<vmsingle>:8428/prometheus/api/v1/label/status_code/values'`
once and write the answer into the vocabulary. UNVERIFIED: the exact unit word VictoriaMetrics appends for `ms`; the
connector README shows `traces_span_metrics_duration_milliseconds_bucket`
after the Prometheus exporter, which follows the same specification.

`service_graph` emits, per `client`, `server`, `connection_type`:
`traces_service_graph_request_total`, `traces_service_graph_request_failed_total`,
`traces_service_graph_request_server` and `traces_service_graph_request_client`
histograms in seconds, `traces_service_graph_unpaired_spans_total`,
`traces_service_graph_dropped_spans_total`. After the naming flag the
histograms read `traces_service_graph_request_server_seconds_bucket`; the
counters keep a single `_total`, the specification adds none when the
name already ends with it.

To feed Grafana's Tempo Service Graph RED table, which reads
`traces_spanmetrics_calls_total` and `traces_spanmetrics_duration_seconds_bucket`,
set `namespace: traces.spanmetrics` and `histogram.unit: s`. Then change the
names in `queries.md` to match. One spelling per installation.

## The vmagent alternative for metrics

vmagent can sit between the collector and VictoriaMetrics, or replace the
collector for metrics alone. Relabeling, stream aggregation and the disk
queue are in `vmagent.md`.

## Rule: connectors and processors rewrite the vocabulary

Every `dimensions` entry is a metric label; it must pass `metrics/labels.md`.
Every `resource`, `attributes`, `transform` or `redaction` action changes
what the stores hold; update the *Backend spelling* column. A checker that
reads the vocabulary cannot see this file.

## Running it locally

```sh
otelcol-contrib validate --config config.yaml
otelcol-contrib --config config.yaml 2> collector.log
```

Its own logs and the `debug` exporter go to stderr.

## Errors, verbatim, and their cause

The store's own message is verbatim. UNVERIFIED: the collector's wrapper
text around an HTTP error, shown here with `...`.

| Log text | Cause |
| --- | --- |
| `Exporting failed. Will retry the request after interval.` with `... 400 Bad Request ...json encoding isn't supported for opentelemetry format. Use protobuf encoding` | `encoding: json` on an exporter; the stores accept protobuf only |
| `Exporting failed. Will retry the request after interval.` with `dial tcp ... connect: connection refused` | nothing listening at the endpoint; wrong host, port or store |
| `... 404 Not Found` | wrong path: `/v1/metrics` instead of `/opentelemetry/v1/metrics`, `/v1/logs` instead of `/insert/opentelemetry/v1/logs`, `/v1/traces` instead of `/insert/opentelemetry/v1/traces`; or the base `endpoint` key used instead of the per signal `*_endpoint` |
| `Exporting failed. Dropping data.` with `Permanent error` | the store answered a 4xx that is not retried; read the body, it is the store's message |
| `data refused due to high memory usage` from `memory_limiter` | over `limit_mib`; the SDK retries |
| `Error: invalid configuration:` with `unknown type: "otlp_http"` or `unknown type: "span_metrics"` | an older contrib binary; use the pre-rename names |
| `Error: invalid configuration:` with `connectors::span_metrics: ...` | the connector is named in `exporters:` of a pipeline whose signal it does not accept; it exports from `traces` and receives into `metrics` only |
| UNVERIFIED: the exact wording of VictoriaMetrics' rejection of a request over `-opentelemetry.maxRequestSize`, default 64 MiB | lower `send_batch_size` |

## Never

- Never leave `debug` with `verbosity: detailed` on in production.
- Never put an id in `dimensions`. Every distinct value is a series.
- Never run two collectors with `service_graph` behind a round robin load
  balancer. A pair split across them is two unpaired spans.
- Never set `encoding: json`.

## Stop and ask

- A dimension is wanted that the vocabulary has no label row for.
- The collector must fan out to a second backend. That is a second exporter
  and a second spelling column.
- Tail sampling is wanted. Read `core/sampling-and-volume.md` first; the
  connectors count only what the sampler kept.
