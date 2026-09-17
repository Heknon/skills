# Grafana and vmui screens: what each one reads

Stamp: Grafana docs `latest` pages Jaeger data source configure and query
editor, Tempo data source additional settings and Service Graph, Node graph
panel; victorialogs-datasource and victoriametrics-datasource READMEs at
main; VictoriaMetrics v1.152.0, VictoriaLogs v1.52.0, VictoriaTraces v0.11.1
docs. Read 2026-09-17.

Read this before a Query task. Column "empty when" lists what makes the
screen blank or wrong. Every field named here has a row in `mapping.md`.

## Data sources behind every screen

| Data source | Plugin id | URL | Notes |
| --- | --- | --- | --- |
| VictoriaMetrics | `victoriametrics-metrics-datasource`, or Grafana's built-in Prometheus type | `http://<victoriametrics-addr>:8428`, cluster `http://<vmselect-addr>:8481/select/<tenant>/prometheus` | with the Prometheus type set "Prometheus type" to `Prometheus` and version to at least `2.24.x` |
| VictoriaLogs | `victoriametrics-logs-datasource` | `http://victorialogs:9428` | `multitenancyHeaders` for `AccountID` and `ProjectID`; `derivedFields` for links |
| Traces, Jaeger | built-in `jaeger` | `http://<victoria-traces>:10428/select/jaeger`, cluster `http://<vtselect>:10471/select/jaeger` | the documented way |
| Traces, Tempo | built-in `tempo` | `http://<victoria-traces>:10428/select/tempo` | experimental on the VictoriaTraces side, minimum v0.9.4; "Save & Test" hits `/select/tempo/api/echo` |

Offline install: extract the plugin archive into the Grafana plugin
directory, `unzip <plugin>.zip -d <plugin dir>/<plugin id>`, then restart.
Or `grafana cli --pluginUrl <url or path to the zip> plugins install
<plugin id>`. The plugin READMEs download
`victoriametrics-metrics-datasource-<ver>.tar.gz` and
`victoriametrics-logs-datasource-<ver>.tar.gz` from the GitHub releases into
`/var/lib/grafana/plugins/`. The plugin READMEs need `allow_loading_unsigned_plugins = <plugin id>` in
`grafana.ini` only for a dev build; a release from the catalog loads
without it.

## The screens

| Screen or panel | Aggregates | Reads | Needs these fields | Produced by these OTLP facts | Empty or wrong when |
| --- | --- | --- | --- | --- | --- |
| Explore > Jaeger > Search | traces by `Service`, `Operation`, `Tags` in logfmt, `Min Duration`, `Max Duration`, `Limit` | `/select/jaeger/api/services`, `/select/jaeger/api/services/{service}/operations`, `/select/jaeger/api/traces` | `resource_attr:service.name`, `name`, `duration`, `span_attr:*` | resource `service.name`; span name; attributes | service list is empty when no span arrived in `-search.streamFieldsLookbehind`, default `72h`; a tag typed with a dot but stored under `resource_attr:` |
| Explore > Jaeger > TraceID, the trace view | one trace as a waterfall; span attributes as tags; process tags from the resource | `/select/jaeger/api/traces/{trace_id}` | `trace_id`, `span_id`, `parent_span_id`, `name`, `kind`, `start_time_unix_nano`, `duration`, `status_code` | context propagated by the SDK | a child whose `parent_span_id` no stored span has; a trace older than `-retentionPeriod`, default `7d`. UNVERIFIED: whether events show as span logs and links as references |
| Jaeger > Node graph, per trace | a graph of the spans of one trace | the same trace | as above | as above | the **Node graph** toggle is off, it "isn't activated by default" |
| Explore > Jaeger > Dependency graph | one node per service, one edge per caller and callee pair with call counts | `/select/jaeger/api/dependencies?endTs=<ms>&lookback=<ms>` | the edges VictoriaTraces computed in its background task | `CLIENT` and `SERVER` spans of two services in one trace; from v0.8.1 also a database client span | VictoriaTraces not started with `-servicegraph.enableTask=true`; the task runs every `-servicegraph.taskInterval`, default `1m0s`, so wait one interval. Experimental on the VictoriaTraces side. UNVERIFIED: the Grafana query type against VictoriaTraces end to end |
| Explore > Tempo > Search and TraceQL | traces by TraceQL such as `{ resource.service.name = "frontend" && status = error }` | `/select/tempo/api/search`, `/select/tempo/api/v2/traces/{trace_id}` | same span fields | same | the VictoriaTraces version is below v0.9.4; a TraceQL function it does not implement |
| Traces Drilldown | rate, error and duration panels over spans | `/select/tempo/api/metrics/query_range` | same | same | experimental; "certain panels or TraceQL capabilities may not function identically to native Grafana Tempo" |
| Explore > Tempo > Service Graph | node graph of services with request rate, error rate and duration | a **Prometheus** data source linked under the Tempo data source's **Service graph > Data source**; it reads `traces_service_graph_request_total`, `traces_service_graph_request_failed_total`, `traces_service_graph_request_server_seconds`, `traces_service_graph_request_client_seconds`; the RED table beside it reads `traces_spanmetrics_calls_total` and `traces_spanmetrics_duration_seconds_bucket` | those series in VictoriaMetrics | the collector's `service_graph` and `span_metrics` connectors, see the chain below | no Prometheus source linked; the series have dots because `usePrometheusNaming` is off; the span metrics namespace is `traces.span.metrics`, which becomes `traces_span_metrics_*`, not `traces_spanmetrics_*`. UNVERIFIED: Grafana's page names Alloy and the Tempo metrics-generator as producers and does not name the collector; the metric names match |
| Dashboard panel on VictoriaMetrics: RED per span name | calls per second, error share, p95 | MetricsQL in `queries.md` over `traces_span_metrics_calls_total` and `traces_span_metrics_duration_milliseconds_bucket` | `service_name`, `span_name`, `span_kind`, `status_code`, `le` | `span_metrics` connector | connector not in the traces pipeline; `status_code` never `STATUS_CODE_ERROR` because span status was left `UNSET` |
| Dashboard panel: Node graph visualization | nodes and edges | two data frames with fields `id` and `id`, `source`, `target` | | | UNVERIFIED: no documented transformation builds those frames from a PromQL result. Use the Tempo data source's Service Graph or the Jaeger Dependency graph instead |
| vmui `:8428/vmui` Explore cardinality | metric names with most series, labels with most series, values per `focusLabel`, `label=name` pairs, labels with most unique values | `/api/v1/status/tsdb` | any | any | it analyses the **current date** by default; pick the day at the top right; narrow with a series selector |
| vmui `:9428/select/vmui` | log lines, hits over time, field names and values | `/select/logsql/query`, `/select/logsql/hits`, `/select/logsql/field_names` | `_msg`, `_time`, `_stream` | any log | wrong tenant headers; the `_time` picker outside the data |
| vmui `:10428/select/vmui`, modes Group, Table, JSON | spans as log entries grouped by stream | `/select/logsql/query` | span fields | any span | as above |
| Explore > VictoriaLogs | log lines with level colouring, ad hoc filters, live tail | `/select/logsql/query`, `/select/logsql/tail` | `_msg`, `_time`, `severity_text`, `trace_id` | the OTLP record | `severity_text` values not recognised by the Log level rules; enable the plugin's **OpenTelemetry preset** to generate them |

## The Dependencies chain, spelled out

Two chains exist. Pick one in the vocabulary and write which.

**Chain A, collector `service_graph` into VictoriaMetrics, read by Grafana's
Tempo data source Service Graph.** Every link must hold.

1. The caller span is `SpanKind.CLIENT` or `SpanKind.PRODUCER` and the callee
   span is `SpanKind.SERVER` or `SpanKind.CONSUMER`, in the same trace, child
   of the caller. The connector pairs "spans with parent-children
   relationship" by kind. An entity controller that is not instrumented is
   reached through a **virtual node**: a `CLIENT` span carrying one of
   `virtual_node_peer_attributes`, default `peer.service`, `db.name`,
   `db.system`, gets a server node named by that value.
2. Both spans pass through **one** collector instance within `store.ttl`,
   default `2s`. Split across instances or late by more than the ttl, they
   count in `traces_service_graph_unpaired_spans_total` and draw nothing.
3. The connector emits `traces_service_graph_request_total{client="<caller
   service.name>", server="<callee service.name or peer.service>",
   connection_type="<unset, messaging_system or database>"}` and the `_failed_total`, `_server`, `_client`
   histograms every `metrics_flush_interval`, default `60s`.
4. The metrics pipeline exports to VictoriaMetrics with
   `-opentelemetry.usePrometheusNaming` on, so the histogram is
   `traces_service_graph_request_server_seconds_bucket` and the counter keeps
   its `_total`. Confirm with the "edges" query in `queries.md`.
5. The Tempo data source's **Service graph > Data source** points at the
   VictoriaMetrics data source; Explore > Tempo > **Service Graph** query
   type draws it.

**Chain B, VictoriaTraces' own graph, read by Grafana's Jaeger data source.**

1. VictoriaTraces runs with `-servicegraph.enableTask=true`; `vtstorage` in
   a cluster. The task walks the last `-servicegraph.taskLookbehind`,
   default `1m0s`, every `-servicegraph.taskInterval`, up to
   `-servicegraph.taskLimit` relations per tenant, default `1000`.
2. Spans of two services share a trace with a client and server pair;
   `-servicegraph.databaseTaskLimit` adds service to database edges from
   client spans carrying `span_attr:db.system.name`.
3. `/select/jaeger/api/dependencies?endTs=<ms>&lookback=<ms>` returns the
   edges; Explore > Jaeger > **Dependency graph** renders them as a node
   graph with call counts. Experimental.

What breaks both: the operation span is `INTERNAL`; there is no callee span
and no `peer.service`; head sampling dropped the trace; `peer.service`
carries an instance id, so one node per instance.

## From a metric to a trace

There are no exemplars in VictoriaMetrics, so no dot on a chart opens a
trace. The route is by labels: read `service_name` and `span_name` off the
series, open Explore > Jaeger > Search with that service and operation and
the panel's time range, sort by duration. Grafana's **Trace to metrics**
setting on the Jaeger data source goes the other way, span to metric, with
`$__tags` mapping span attribute names to label names; map `service.name` to
`service_name` there.

## From a trace to logs, and back

- **Logs to trace.** VictoriaLogs data source, **Derived fields**: `name`
  `trace_id`, `matcherType: label`, `matcherRegex: trace_id`,
  `url: '${__value.raw}'`, `datasourceUid: <the Jaeger data source uid>`. The
  plugin's **OpenTelemetry preset** creates this and the level rules for
  `severity_text`; its `tracesDatasourceUid` accepts only Jaeger today.
- **Trace to logs.** On the Jaeger data source, **Trace to logs** with
  **Use custom query** and the query
  `trace_id:="${__trace.traceId}" AND span_id:="${__span.spanId}"`. The
  VictoriaLogs plugin README says this works since Grafana v12.2.0.
  UNVERIFIED: Grafana's own page still says "You can select Loki or Splunk
  logs data sources" for the target.
- **Logs to logs.** A derived field whose target is the VictoriaLogs data
  source and whose `url` is a LogsQL query such as `trace_id:${__value.raw}`.

## Never

- Never judge from an empty Service Graph that spans are missing. It reads
  VictoriaMetrics, not VictoriaTraces.
- Never expect a span event on the Grafana waterfall until you have opened
  one trace and seen it. The mapping is UNVERIFIED.
- Never read the cardinality explorer for yesterday without changing its
  date.

## Stop and ask

- The Service Graph is wanted and the vocabulary says
  `usePrometheusNaming` is off.
- Someone wants a per trace view richer than the Jaeger waterfall. The
  VictoriaTraces roadmap lists its own trace UI as future work.
