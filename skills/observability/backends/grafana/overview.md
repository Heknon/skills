# Grafana stack: the path from SDK to screen

Stamp: Grafana 13.2 docs, Tempo 3.0 docs (Tempo v2.8.x docs where a line says
2.8), Loki 3.7 docs, Prometheus 3.14.0 docs and CHANGELOG, Mimir 3.2 docs,
opentelemetry-collector-contrib READMEs at main, Grafana Alloy docs at latest,
read 2026-09-17. Facts taken from source rather than a docs page are marked
`source:`. The coordinator asked for Grafana 11 or 12, Tempo 2.x and Mimir 2.x;
`latest` now serves one major newer, and every line that differs on the older
major says so.

## The hops

```
OpenTelemetry SDK --OTLP--> [Collector or Alloy, optional] --OTLP--> Tempo      (traces)
                                                          --OTLP--> Loki       (logs)
                                                          --OTLP--> Prometheus (metrics)
                                                                    or Mimir
Tempo metrics-generator --remote_write--> Prometheus or Mimir       (derived RED, service graph)
Grafana data sources: Tempo, Loki, Prometheus --> Explore, dashboards, Drilldown apps
```

1. **SDK.** Exports spans, metrics and logs over OTLP. An unsampled span is
   never exported, so nothing downstream sees it.
2. **Collector.** Optional. Forwards OTLP as OTLP with one exporter per store.
   See `collector.md`. Grafana Alloy is the Grafana build of the same
   collector; its components are `otelcol.receiver.otlp`,
   `otelcol.exporter.otlphttp` and friends. Without a collector the SDK sends
   to the three stores directly, three exporters, three endpoints.
3. **Tempo.** Stores traces. Its distributor embeds the collector's OTLP
   receiver: `distributor.receivers.otlp.protocols.grpc` default
   `localhost:4317`, `http` default `localhost:4318`. The HTTP path is the
   OTLP standard `/v1/traces`. Query API on `:3200`.
4. **Loki.** Stores logs. `POST /otlp/v1/logs` on `:3100`. The collector's
   `otlphttp` exporter is pointed at `http://<loki>:3100/otlp` and appends
   `/v1/logs` itself.
5. **Prometheus or Mimir.** Stores metrics. Prometheus:
   `POST /api/v1/otlp/v1/metrics` on `:9090`, only with the flag
   `--web.enable-otlp-receiver`. Mimir: `POST /otlp/v1/metrics` on `:8080`.
   Both also accept Prometheus remote write, which is what Tempo's
   metrics-generator speaks: Prometheus `POST /api/v1/write` with
   `--web.enable-remote-write-receiver`, Mimir `POST /api/v1/push`.
6. **Grafana.** Reads all three through data sources and joins them with
   links: trace to logs, trace to metrics, logs to traces, exemplars to
   traces. Grafana stores nothing of the telemetry.

Tenancy: Loki and Mimir read the tenant from the `X-Scope-OrgID` header.
Loki's `auth_enabled` defaults to `true`, so a push without the header is
refused. Mimir with `-auth.multitenancy-enabled=false` uses the tenant
`anonymous`. UNVERIFIED: Tempo's key is `multitenancy_enabled`, default false.

## Where each signal lands

| Store | Holds | Written by | Read with |
| --- | --- | --- | --- |
| Tempo | every span, event, link and attribute, as sent, in Parquet blocks | distributor, per OTLP span | TraceQL, `GET /api/traces/<id>`, `GET /api/search?q=` |
| Loki | log records: index labels, structured metadata, body | `/otlp/v1/logs` | LogQL, `GET /loki/api/v1/query_range` |
| Prometheus or Mimir | metrics you emit, translated to Prometheus names | OTLP endpoint | PromQL, `GET /api/v1/query` |
| Prometheus or Mimir | `traces_spanmetrics_*`, `traces_service_graph_*` derived from spans | Tempo metrics-generator over remote write, or the collector's connectors | PromQL, and Grafana's Service Graph view |

There is no error store. An exception is a span event named `exception` in
Tempo, or a log line with `severity_text=ERROR` in Loki. There is no
aggregated transaction store either. Every count and latency over spans comes
from a metrics-generator series or from a TraceQL metrics query at read time.

## What a root span is called here

Nothing. Tempo has no transaction document. A root span is a span whose parent
id is empty, and TraceQL exposes it through the trace intrinsics
`trace:rootName` and `trace:rootService`. `{ trace:rootName = "tests/a.py::test_x" }`
selects whole traces by their root. The kind of the root span matters more
than in Elastic: Grafana's span metrics table filters
`span_kind="SPAN_KIND_SERVER"` by default and the service graph pairs
`client` with `server` spans, so an `INTERNAL` root is invisible to both until
you change the filter or the kind. See `screens.md`.

## The data model in five lines

1. Tempo keeps the OTLP span whole: name, kind, status, every attribute with
   its type and its dotted key, events, links, resource, scope. Query scope
   decides where a key is looked up: `resource.`, `span.`, `event.`, `link.`,
   `instrumentation.`.
2. Loki splits a log record into stream **labels**, a short fixed list of
   resource attributes with dots turned to underscores, **structured
   metadata**, everything else including `trace_id` and `span_id`, and the
   **body**.
3. Prometheus turns each OTLP metric into a series family: dots to
   underscores, unit suffix and `_total` appended, resource attributes into
   `target_info` plus `job` and `instance`, everything cumulative.
4. Derived RED and dependency metrics are ordinary Prometheus series produced
   by one component you choose, never two.
5. Grafana joins the three by `trace_id` and by label values, configured per
   data source. Nothing joins by itself.

## Where derivation happens

Elastic derives transaction and dependency metrics on the server from every
span, always, and Kibana reads only those. Here **nothing is derived unless
you turn it on**, and there are two places that can do it:

| Place | Processors | Metric names | Enable with |
| --- | --- | --- | --- |
| Tempo metrics-generator | `span-metrics`, `service-graphs` | `traces_spanmetrics_calls_total`, `traces_spanmetrics_latency_bucket`, `traces_service_graph_request_total`, ... | `overrides.defaults.metrics_generator.processors` plus `metrics_generator.storage.remote_write` |
| Collector connectors | `span_metrics`, `service_graph` | `traces_span_metrics_calls_total`, `traces_span_metrics_duration_milliseconds_bucket`, `traces_service_graph_request_total`, ... | `connectors:` plus a metrics pipeline, see `collector.md` |

**Decision rule.** One place, written into `vocabulary.md` under *Metrics* as
`derived by: Tempo metrics-generator` or `derived by: collector connectors`,
the same words as the `span metrics derived by` line in `backends/README.md`.

- Tempo receives every span, no sampler before it: **metrics-generator**.
  Grafana's Service Graph view and span metrics table are built for its
  names and labels, and exemplars come free because traces and metrics meet
  in one process.
- A sampler runs before Tempo, `tail_sampling` or `probabilistic_sampler` in
  the collector: **collector connectors**, placed in a pipeline that runs
  before the sampler, so the counts are of all spans and Tempo holds the
  sampled subset. Grafana's built-in views then need the names remapped;
  `screens.md` says where.
- Both on at once is two series families counting every span, and any
  dashboard that sums across them is double. Invariant 8.

## Tempo 3.0 versus 2.x

Tempo 3.0 removed the ingester and the compactor; recent data is served by the
`live-store`, blocks are built by the `block-builder`, and compaction runs in
the `backend-scheduler` and `backend-worker`. Monolithic mode is `-target=all`
and needs no Kafka. 3.0 also removed the `local-blocks` processor and refuses
to start on the legacy flat overrides format; migrate with
`tempo-cli migrate overrides-config`. TraceQL metrics queries are served
without any generator processor in 3.0. On 2.8 they need
`overrides.defaults.metrics_generator.processors: [local-blocks]` and
`metrics_generator.processor.local_blocks.flush_to_storage: true`. Metric
names from `span-metrics` and `service-graphs` are the same on both majors.

## How to read the running version

Read every component. Compare with the stamp above before trusting a field.

| Component | Endpoint or command | Field to read |
| --- | --- | --- |
| Grafana | `GET /api/health` | `version` |
| Grafana, more detail | `GET /api/frontend/settings` | `buildInfo.version` |
| Grafana, on the host | `grafana cli -v` | the printed version |
| Tempo | `GET :3200/api/status/buildinfo` | `version` |
| Tempo, is it up | `GET :3200/ready`, `GET :3200/api/echo` | HTTP 200 |
| Loki | `GET :3100/loki/api/v1/status/buildinfo` | `version` |
| Loki, is it up | `GET :3100/ready` | HTTP 200 |
| Prometheus | `GET :9090/api/v1/status/buildinfo` | `data.version` |
| Prometheus, flags in effect | `GET :9090/api/v1/status/flags` | `web.enable-otlp-receiver`, `enable-feature` |
| Mimir | `GET :8080/prometheus/api/v1/status/buildinfo` | `data.version` |
| Mimir, is it up | `GET :8080/ready` | HTTP 200 |
| Collector | `otelcol-contrib --version` | the printed version. source: `otelcol/command.go` sets cobra `Version` |
| Alloy | the UI at `http://localhost:12345` | UNVERIFIED: where the UI prints the version; the home page lists components and health |

## Never

- Never turn on the metrics-generator and the collector connectors for the
  same spans. Two families, double counts.
- Never expect a screen to aggregate spans by itself. Every RED chart reads a
  series something produced, or runs a TraceQL metrics query you wrote.
- Never point the SDK's metrics at Prometheus without
  `--web.enable-otlp-receiver`. The endpoint returns 404 and the SDK logs it
  once per export.

## Stop and ask

- The installation runs Grafana Cloud features, Application Observability,
  Adaptive Metrics, Adaptive Traces. This folder covers self-hosted, air-gapped
  installs only. See `screens.md`.
- The running Tempo is 2.x and TraceQL metrics are wanted. The `local-blocks`
  path above is verified on 2.8 docs only; a person confirms the minor.
