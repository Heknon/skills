# Victoria stack: the path from SDK to screen

Stamp: VictoriaMetrics v1.152.0 and vmagent v1.152.0, LTS line v1.148.x;
VictoriaLogs v1.52.0; VictoriaTraces v0.11.1; Grafana docs `latest`;
opentelemetry-collector-contrib component READMEs at `main`. Read
2026-09-17 at docs.victoriametrics.com, grafana.com/docs and the component
READMEs. Facts taken from source rather than a doc page are marked
`source:` with the file.

## The hops

```
OpenTelemetry SDK --OTLP/HTTP protobuf--> [Collector, optional] --OTLP/HTTP protobuf-->
   metrics: VictoriaMetrics :8428  /opentelemetry/v1/metrics
            (or vmagent :8429 same path, then remote write to VictoriaMetrics)
   logs:    VictoriaLogs    :9428  /insert/opentelemetry/v1/logs
   traces:  VictoriaTraces  :10428 /insert/opentelemetry/v1/traces  (also OTLP/gRPC when enabled)
   --> Grafana data sources: victoriametrics-metrics-datasource, victoriametrics-logs-datasource,
       Jaeger data source at http://<victoria-traces>:10428/select/jaeger
   --> built-in UIs: /vmui on :8428, /select/vmui on :9428 and :10428
```

1. **SDK.** Exports spans, metrics and logs over OTLP. Use OTLP/HTTP with
   protobuf. JSON encoding is rejected by all three stores: the getting
   started guide lists "VictoriaMetrics and VictoriaLogs do not support
   experimental JSON encoding" as a limitation, and VictoriaLogs answers
   `json encoding isn't supported for opentelemetry format. Use protobuf
   encoding` (source: `app/vlinsert/opentelemetry/opentelemetry.go`).
   An unsampled span is never exported, so no store sees it.
2. **Collector.** Optional for the bare hops. **Required for RED and
   dependency views**, because nothing in this stack derives a metric from a
   span. See `collector.md` for `span_metrics` and `service_graph`.
3. **Three stores, three binaries, three ports.** Each is one executable
   with no external dependency. Each accepts OTLP for exactly one signal.
   There is no shared "server" component and no shared authentication; put
   `vmauth` or a proxy in front when you need auth.
4. **Grafana**, or the built-in vmui pages. Grafana needs two plugins
   installed offline plus the bundled Jaeger data source.

## Where each signal lands

| Store | Holds | Unit of storage | Ingest path | Query path |
| --- | --- | --- | --- | --- |
| VictoriaMetrics single-node | every OTLP metric data point, plus everything the collector connectors compute | a time series: metric name plus label set | `POST :8428/opentelemetry/v1/metrics` | `:8428/prometheus/api/v1/query`, `/api/v1/query_range`, `/api/v1/series`, `/api/v1/export`, `/api/v1/labels`, `/api/v1/label/<name>/values`, `/api/v1/status/tsdb` |
| VictoriaMetrics cluster | same | same | `POST http://<vminsert>:8480/insert/<accountID>/opentelemetry/v1/metrics` | `http://<vmselect>:8481/select/<accountID>/prometheus/api/v1/...` |
| vmagent | nothing; relays and can aggregate | same | `POST :8429/opentelemetry/v1/metrics` then `-remoteWrite.url` | none; it has `/metrics` and `/targets` only |
| VictoriaLogs | every OTLP log record | a log entry: `_msg`, `_time`, `_stream`, arbitrary fields | `POST :9428/insert/opentelemetry/v1/logs` | `:9428/select/logsql/query` and friends |
| VictoriaTraces | every OTLP span, stored as one VictoriaLogs entry each | a log entry whose fields are the span | `POST :10428/insert/opentelemetry/v1/traces`; OTLP/gRPC at `-otlpGRPCListenAddr=:4317` | `:10428/select/jaeger/api/...`, `:10428/select/logsql/query`, experimental `:10428/select/tempo/api/...` |

`<accountID>` is a 32-bit integer or `accountID:projectID`; `projectID`
defaults to `0`. VictoriaLogs and VictoriaTraces take the tenant from the
`AccountID` and `ProjectID` request headers instead, default `0` and `0`.

## The data model in five lines

1. A **metric** is a name plus labels plus float samples. Labels are strings.
   Nothing else has a type.
2. A **log entry** is a flat set of string fields. Three are special: `_msg`,
   `_time`, and `_stream`, which is the small label set that groups entries
   into a stream. Every other field is indexed for search as it is.
3. A **span** is a log entry in VictoriaTraces. Its stream is
   `{name="<span name>",resource_attr:service.name="<service>"}`. Resource
   attributes are fields prefixed `resource_attr:`, span attributes
   `span_attr:`, events `event:...:<index>`, links `link:...:<index>`.
4. Dots are kept in log and span field names, and in metric names and label
   names unless a naming flag rewrites them. Nested attribute maps flatten
   with `.`.
5. Nothing is derived across signals. A count of spans, a latency percentile
   per span name, an edge between two services: each exists only if the
   collector computed it and wrote it into VictoriaMetrics.

## What a root span is called here

Nothing. There is no transaction and no span document kind. VictoriaTraces
stores every span the same way, and a root span is the entry whose
`parent_span_id` field is empty. The Jaeger API returns the whole trace and
Grafana draws the span without a parent at the top. Every per-unit-of-work
aggregate, latency distribution, failure rate, throughput, comes from the
collector's `span_metrics` connector filtered on `span_kind` or on the root
span's name. See `screens.md`.

## Where derivation happens: the contrast with Elastic

Elastic's APM Server reads every span it receives and writes transaction,
service destination and service summary metrics on its own. This stack has
no such component. VictoriaMetrics stores what it is sent. VictoriaTraces
stores spans and answers Jaeger queries over them. So:

- RED per service and per span name exist only if the collector's
  `span_metrics` connector writes `traces.span.metrics.calls` and
  `traces.span.metrics.duration` into VictoriaMetrics.
- Service dependencies exist in two forms. The collector's `service_graph`
  connector writes `traces_service_graph_request_total{client, server,
  connection_type}` into VictoriaMetrics, or VictoriaTraces builds its own
  experimental graph for `/select/jaeger/api/dependencies` when started with
  `-servicegraph.enableTask=true`.
- vmagent stream aggregation, `-streamAggr.config`, derives rates, totals,
  quantiles and `vmrange` histograms from **metrics** the SDK already emits.
  It never reads a span.

`metrics/derived-or-emitted.md` therefore returns **stop and ask** on this
stack whenever no connector is enabled.

## How OTLP metrics are renamed, in one paragraph

By default VictoriaMetrics stores OTLP metric points "as is without any
transformations": `process.cpu.time{service.name="foo"}` stays
`process.cpu.time{service.name="foo"}`. With
`-opentelemetry.usePrometheusNaming` it becomes
`process_cpu_time_seconds_total{service_name="foo"}`. Every resource
attribute is promoted to a label on every point by default. There is no
`job`, no `instance` and no `target_info`. `mapping.md` has the rules.
Decide the flag once, before the first sample, and write the resulting
spelling into the vocabulary.

## How to read the running version

Read every component the installation runs. Compare each with the stamp at
the top of the file you are about to use.

| Component | Endpoint, flag or command | Field to read |
| --- | --- | --- |
| VictoriaMetrics single-node | `curl http://<vmsingle>:8428/metrics \| grep vm_app_version` | the `version` label of `vm_app_version`; the vmagent guide says it is "emitted by all VictoriaMetrics components" |
| VictoriaMetrics single-node, cluster components | `./victoria-metrics -version`, and the same flag on `vminsert`, `vmselect`, `vmstorage` | prints the version; flag help: "Show VictoriaMetrics version" |
| vmagent | `curl http://<vmagent>:8429/metrics \| grep vm_app_version`, or `./vmagent -version` | as above |
| VictoriaLogs | `curl http://<victorialogs>:9428/metrics \| grep vm_app_version` | UNVERIFIED: the VictoriaLogs metrics reference page does not list a version metric; the components share the VictoriaMetrics build info library. Confirm on `/metrics`, and fall back to the startup log line |
| VictoriaTraces | `curl http://<victoria-traces>:10428/metrics \| grep vm_app_version`, or the first log line `starting VictoriaTraces at "[:10428]"` | UNVERIFIED as for VictoriaLogs |
| Grafana | `GET http://<grafana>:3000/api/health` | `version`, for example `{"commit":"...","database":"ok","version":"..."}` |
| Grafana plugins | **Administration > Plugins and data > Plugins**, or `grafana cli plugins ls` | the version beside `victoriametrics-metrics-datasource` and `victoriametrics-logs-datasource` |
| Collector | UNVERIFIED: `otelcol-contrib --version`. Verified instead: its own telemetry at `http://127.0.0.1:8888/metrics` carries resource attribute `service.version` | the version string |

## Never

- Never send OTLP/JSON to any of the three stores.
- Never expect a metric to appear because a span arrived. Check
  `collector.md` for the connector that writes it.
- Never point the SDK's traces at VictoriaLogs or its logs at
  VictoriaTraces. Each store accepts one signal on one path and answers
  the wrong signal with an HTTP error.
- Never treat VictoriaTraces as fixed. Its roadmap lists "Finalize the data
  structure and commit to backward compatibility" as work still to do
  before general availability.

## Stop and ask

- The installation runs VictoriaMetrics below v1.132.0 and the SDK exports
  delta temporality. Delta values are stored as is only from v1.132.0.
- The installation has no collector and someone asks for a latency chart
  per test or a dependency view. Nothing here will draw it.
- The VictoriaTraces version is not 0.11.x. Field names in this folder come
  from that line and the roadmap says they may change.
