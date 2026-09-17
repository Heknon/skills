# Grafana screens: what each one reads

Stamp: Grafana 13.2 docs pages Tempo data source, Service graph, Trace to
logs, Additional settings, Provision, Loki data source, Prometheus data source,
Explore trace view, Traces Drilldown access, Plugin install, CLI; the
`grafana/grafana-tempo-datasource` source `src/graphTransform.ts` at main for
the exact PromQL the frontend runs; read 2026-09-17.

Read this before a Query task. Column "empty when" lists what makes a panel
blank or wrong. Every row's fields have a row in `mapping.md`.

## Data sources behind every screen

Three data sources, provisioned once. Nothing joins them until these are set:

- **Tempo** data source, URL `http://tempo:3200`. `jsonData.serviceMap.datasourceUid`
  names the Prometheus data source that holds the generator's series.
  `jsonData.tracesToLogsV2` and `jsonData.tracesToMetrics` build the links
  from a span. `jsonData.nodeGraph.enabled: true` shows the trace as a graph.
- **Loki** data source, URL `http://loki:3100`. `jsonData.derivedFields` with
  `matcherType: label`, `matcherRegex: trace_id`, `datasourceUid: <tempo uid>`,
  `url: ${__value.raw}` builds the link from a log line to its trace. The UI
  calls the type **Label**; UNVERIFIED: `label` as the provisioning value of
  `matcherType`, the docs page shows only the `regex` form.
  Multi-tenant Loki needs the custom header `X-Scope-OrgID`.
- **Prometheus** data source, URL `http://prometheus:9090` or
  `http://mimir:8080/prometheus`. `jsonData.exemplarTraceIdDestinations:
  [{name: trace_id, datasourceUid: <tempo uid>}]` turns an exemplar into a
  link. Set `prometheusType` and `prometheusVersion` so the query builder
  knows the dialect.

## The screens

| Screen or panel | Aggregates | Reads | Needs | Produced by these OTLP facts | Empty or wrong when |
| --- | --- | --- | --- | --- | --- |
| Explore, Tempo, **Search** builder | nothing; lists matching traces with Trace ID, name, start, duration | Tempo `/api/search` | `resource.service.name`, `span:name`, any attribute | resource `service.name`; span names | time range past retention; `search.hide` set; tag values list empty because no trace in range |
| Explore, Tempo, **TraceQL** | whatever the query says, including `count()`, `avg(span:duration)`, `rate()`, `quantile_over_time()` | Tempo `/api/search`, `/api/metrics/query_range` | the scoped keys in `mapping.md` | the attributes as sent | wrong scope: `span.service.name` finds nothing, it is `resource.service.name`; a quoted value against a numeric attribute |
| Trace view | the waterfall of one `trace:id`: name, duration, critical path, span details with attributes, resource attributes, events, links | Tempo `/api/v2/traces/<id>` | `span:parentID`, `link:traceID` | context propagated by the SDK; links for the session root | a child whose parent id no span has, from broken propagation; trace not found after `max_bytes_per_trace` cut it |
| Span details, **Logs for this span** icon | nothing; runs the trace-to-logs query in a split | Loki, the Tempo data source's `tracesToLogsV2` | the `tags` mapping, `filterByTraceID`, `filterBySpanID` | `trace_id` in Loki structured metadata; `service.name` on the log resource | the tag mapping still says `service.name` instead of `service_name`; logs sent without trace context; time shift too narrow for a late log |
| Span details, trace to metrics link | the PromQL in `tracesToMetrics.queries` with `$__tags` filled from the span | Prometheus | the `tags` mapping, e.g. `service.name` to `service` | span metrics series with matching label values | the label name on the series differs from the mapping: `service` for the generator, `service_name` for the connector |
| Explore, Tempo, **Service Graph** node graph | nodes per `client` and `server` value, edges with rate, error rate, latency | Prometheus `traces_service_graph_request_total`, `_failed_total`, `_server_seconds_sum`, `_server_seconds_bucket` | `serviceMap.datasourceUid` | `CLIENT` and `SERVER` span pairs across services, or a `CLIENT` span with `peer.service` for a virtual node | the generator's `service-graphs` processor off; both sides in one process with no `SERVER` span and no `peer.service`; `wait` too short so the pair expired |
| Service Graph **span metrics table**, under the node graph | rate, error rate, p90 per `span_name` | `sum(rate(traces_spanmetrics_calls_total{}[$__range])) by (span_name)`, `histogram_quantile(.9, sum(rate(traces_spanmetrics_latency_bucket{}[$__range])) by (le))`, default filter `span_kind="SPAN_KIND_SERVER"` | the generator's `span-metrics` processor | `SERVER` spans | root spans are `INTERNAL`: filter them out by default; the series are named `traces_span_metrics_*` because the collector made them; Grafana's Tempo troubleshooting page says newer Tempo may emit `traces_spanmetrics_duration_seconds_bucket` and the duration column is then blank |
| Explore, Loki | log lines, or a LogQL metric | Loki | labels and structured metadata from `mapping.md` | resource `service.name`; record attributes | stream selector on a structured metadata key; `service_name` misspelled `service.name` |
| Log line, derived field link | nothing; opens Tempo with the `trace_id` value | Loki, then Tempo | `derivedFields` with `matcherType: label` on `trace_id` | `TraceId` on the log record | derived field configured as a regex over the body while the id is metadata; trace past Tempo retention |
| Prometheus panel with **Exemplars** on | dots on the chart, each a `trace_id` | Prometheus `/api/v1/query_exemplars` | `exemplarTraceIdDestinations`, `--enable-feature=exemplar-storage` | histogram data points with exemplars from the SDK, or `send_exemplars: true` on the generator's `remote_write` | Prometheus without the flag; the panel query is not over a histogram or counter that carries them |
| **Drilldown > Traces** | RED per service and span, breakdowns by attribute, queryless | Tempo TraceQL metrics | Grafana 11.6+, bundled from 12; Tempo 2.6+ with TraceQL metrics configured | every span; nothing extra | Tempo 2.x without the `local-blocks` processor; the Grafana is 11.x without `grafana-exploretraces-app` installed |
| **Drilldown > Logs** | volume by `detected_level` and `service_name`, patterns | Loki | `discover_log_levels`, `discover_service_name` | resource `service.name` | `service_name` missing so everything is `unknown_service` |

## The Dependencies chain, spelled out

Elastic's Dependencies screen is this stack's Service Graph plus a per-peer
RED panel you build. Every link must hold.

1. The span is an exit span: `SpanKind.CLIENT` or `PRODUCER`, with a parent.
2. The span carries `peer.service=<definition name>`. Tempo's generator lists
   `peer.service`, `db.name`, `db.system`, and on 3.0 `db.system.name`, in
   `peer_attributes`; the first present names the virtual node. The
   collector's `service_graph` reads `virtual_node_peer_attributes`, same
   defaults minus `db.system.name`.
3. The producer is on. Generator: `overrides.defaults.metrics_generator.processors`
   contains `service-graphs`, and `metrics_generator.storage.remote_write`
   points at the Prometheus. Collector: `service_graph` is in a traces
   pipeline's `exporters` and a metrics pipeline's `receivers`.
4. The pair completes inside `wait` (generator default `10s`) or `store.ttl`
   (connector default `2s`), and the store holds under `max_items` (generator
   `10000`, connector `1000`). A `CLIENT` span with no matching `SERVER` span
   becomes an edge to a virtual node named by step 2, or counts in
   `traces_service_graph_unpaired_spans_total` when step 2 also fails.
5. Prometheus has a series `traces_service_graph_request_total{client="sahara-harness", server="tank", connection_type="virtual_node"}`
   within one `collection_interval`, default `15s`, plus the remote write lag.
6. Grafana's Tempo data source has `serviceMap.datasourceUid` set to that
   Prometheus. The node graph draws `sahara-harness` to `tank`.

Per-peer latency and failure rate are not on the node graph's edge only; build
the panel: `queries-promql.md`, "Dependencies, RED per peer".

What breaks it: `INTERNAL` on the operation span; no `peer.service`; the
instance id in `peer.service`, one node per instance; head sampling in the
SDK before Tempo, the generator counts the sampled set; the generator on one
tenant and the query on another, `remote_write_add_org_id_header` is `true`
by default and stamps the tenant.

## Dashboards to build first

In this order. Each is a Prometheus panel over the generator's series; swap
`traces_spanmetrics_` for `traces_span_metrics_` and `service` for
`service_name` when the collector produced them.

1. **RED per service.** Rate
   `sum by (service) (rate(traces_spanmetrics_calls_total[5m]))`, errors
   `sum by (service) (rate(traces_spanmetrics_calls_total{status_code="STATUS_CODE_ERROR"}[5m]))`,
   duration `histogram_quantile(0.95, sum by (service, le) (rate(traces_spanmetrics_latency_bucket[5m])))`.
   Filter `span_kind` to the unit of work's kind.
2. **Service graph.** The Explore view, or a Node graph panel with the same
   four series.
3. **Per-label latency.** Add the label to `dimensions` first, then
   `histogram_quantile(0.95, sum by (sahara_entity_definition, le) (rate(traces_spanmetrics_latency_bucket{span_name="entity.create"}[5m])))`.
4. **Logs by level per service.** `sum by (service_name, detected_level) (count_over_time({service_name=~".+"}[5m]))`.

## Do not rely on these in a self-hosted, air-gapped install

Application Observability, Adaptive Metrics, Adaptive Traces and Logs, the
Grafana Cloud OTLP gateway, Grafana Cloud's Loki config self-serve API, the
Kubernetes Monitoring app, hosted Pyroscope. They are Grafana Cloud products
or need a connection out. The Drilldown apps are bundled in Grafana 12 and
later and run offline. On 11.x install them from a zip:
`grafana cli --pluginUrl file:///path/grafana-exploretraces-app.zip plugins install grafana-exploretraces-app`
or `unzip <plugin>.zip -d /var/lib/grafana/plugins/<plugin-id>` and restart.
UNVERIFIED: that `--pluginUrl` accepts a `file://` URL; the docs show an
https URL on a private host. `grafana.ini` `[plugins] preinstall` also takes
`<id>@<version>@<url>`.

## Never

- Never judge from the span metrics table that spans are missing. It reads
  Prometheus, filtered to `SPAN_KIND_SERVER`.
- Never expect a span event on the Service Graph or in Loki. It is inside the
  span in Tempo.
- Never set `tracesToLogsV2.tags` to `service.name` without the `value:
  service_name` mapping. Loki has no label with a dot.

## Stop and ask

- The unit of work's root span is `INTERNAL` and the span metrics table must
  show it. Changing the kind to `SERVER` is a vocabulary change.
- A node appears twice, once as a service and once as a virtual node, because
  `peer.service` differs from the callee's `service.name`.
