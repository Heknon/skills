# Verification ladder

Stamp: VictoriaMetrics v1.152.0, VictoriaLogs v1.52.0, VictoriaTraces
v0.11.1, opentelemetry-python 1.2x, collector contrib at `main`, read
2026-09-17.

**Verdict you produce:** the number of the last rung where the span is seen,
1 to 4, and the first rung where it is missing or changed. Write it as
`last seen: rung N` at the top of your answer, then fix that hop only.

One span, pushed through every hop, bottom up. Do not skip a rung. A span
right at rung 2 and missing at rung 3 is a store problem, not an SDK one.

Pick the span first. Use the harness's own unit of work: one test, so one
root span with at least one CLIENT span under it. Note the values you will
look for: `trace_id`, the root span's `span_id`, one attribute such as
`sahara.cycle.id`, and the CLIENT span's `peer.service`. Note also one metric
name and one log line the same test produced, because on this stack each
signal has its own store and its own rung 3.

## Rungs 1 and 2: the SDK and the collector

Rungs 1 and 2 are the same on every backend and live in
`backends/ladder-rungs-1-2.md`. Run them first; start here only with the span
seen at rung 2, or at rung 1 when there is no collector.

## Rung 3: the stores

Three stores, three calls. Ids are lowercase hex without `0x`.

**The span, VictoriaTraces:**

```sh
curl http://<victoria-traces>:10428/select/logsql/query -d 'query=trace_id:="4bf92f3577b34da6a3ce929d0e0e4736" _time:1h | sort by (start_time_unix_nano)'
```

One JSON line per span. Check in the root's line: `parent_span_id` absent,
`name` equal to the span name, `kind` `1`, `status_code` `2` for a failed
test, `span_attr:sahara.cycle.id`, `span_attr:sahara.environment.id`,
`span_attr:sahara.worker.id`, `span_attr:test.nodeid_hash`, `resource_attr:deployment.environment`, and
`_stream` equal to
`{name="tests/test_one.py::test_create",resource_attr:service.name="sahara-harness"}`.
In the CLIENT line: `kind` `3`, `parent_span_id` equal to the root's
`span_id`, `span_attr:peer.service`. Keys are dotted with a prefix now.

Then through the API Grafana uses:

```sh
curl http://<victoria-traces>:10428/select/jaeger/api/traces/4bf92f3577b34da6a3ce929d0e0e4736
```

**The metric, VictoriaMetrics**, after one `metrics_flush_interval` plus the
`-search.latencyOffset` default `30s`:

```sh
curl 'http://<vmsingle>:8428/prometheus/api/v1/series' -d 'match[]=traces_span_metrics_calls_total{service_name="sahara-harness",span_name="tests/test_one.py::test_create"}'
curl 'http://<vmsingle>:8428/api/v1/export' -d 'match[]=traces_span_metrics_calls_total{service_name="sahara-harness"}' -d 'start=-1h'
```

Cluster: the same suffixes under `http://<vmselect>:8481/select/0/prometheus/`.
The `series` call shows the full label set as stored; compare every label
name with the vocabulary's spelling column. A name with a dot here means
`-opentelemetry.usePrometheusNaming` is off on the store that received it.
No series at all: `curl 'http://<vmsingle>:8428/prometheus/api/v1/labels'`
lists what did arrive today. UNVERIFIED: the name of the ingestion counter
on `http://<vmsingle>:8428/metrics` that would show whether any OTLP sample
arrived; read the `/metrics` page for a `_rows_inserted_total` counter.

The dependency edge, after the `service_graph` flush:

```sh
curl 'http://<vmsingle>:8428/prometheus/api/v1/series' -d 'match[]=traces_service_graph_request_total{client="sahara-harness"}'
```

No hit with the span present means the CLIENT span had no SERVER child and
no `peer.service`, or the pair missed `store.ttl`.

**The log line, VictoriaLogs:**

```sh
curl http://<victorialogs>:9428/select/logsql/query -d 'query=trace_id:="4bf92f3577b34da6a3ce929d0e0e4736" _time:1h' -d 'limit=50'
```

Check `_msg`, `_time`, `severity_text`, `span_id`, `sahara.cycle.id`, and that
`_stream` holds only the fields you named in `VL-Stream-Fields`. Nothing at
all: `curl http://<victorialogs>:9428/select/logsql/query -d 'query=*' | head`
and `curl http://<victorialogs>:9428/metrics | grep vl_rows_ingested_total`.
Send one request with `VL-Debug: 1` and read the store's log to see what it
parsed; the rows are logged and not stored. VictoriaTraces has the same
switch as `VT-Debug: 1` and `debug=1`.

When nothing arrives, the store's console output is the witness.
VictoriaTraces documents that it "emits its own logs to stdout"; read the
same place for the other two. Look for `cannot read
OpenTelemetry protocol data`, `json encoding isn't supported`, and the
`WARNING` sample that `-storage.maxHourlySeries` prints when it drops.
`-logIngestedRows` on VictoriaLogs or VictoriaTraces prints every entry.

## Rung 4: Grafana

The screen names are in `screens.md`. For this ladder: Explore > Jaeger >
TraceID with `4bf92f3577b34da6a3ce929d0e0e4736` must draw the CLIENT span
under the test span. Explore > VictoriaLogs with
`trace_id:="4bf92f3577b34da6a3ce929d0e0e4736"` must list the lines and show
the derived `trace_id` link. A VictoriaMetrics panel with the p95 query from
`queries.md` must have the span name in its legend. Grafana shows only what
rung 3 holds. A span in rung 3 and absent here is a time picker, a data
source URL missing `/select/jaeger`, a tenant header, or the
`-search.streamFieldsLookbehind` window on the service dropdown, never lost
data.

## Symptom to rung

| Symptom | First rung to check | Usual cause |
| --- | --- | --- |
| trace missing entirely | 1 | span never ended, or process exited before `force_flush`; then 3 for a 4xx in the collector log |
| span present, no dependency edge | 3, the `traces_service_graph_request_total` query | not `SpanKind.CLIENT`, no `peer.service`, no SERVER child, pair split across collectors, or under one flush interval old |
| span present, no RED series | 2, the connector block in `backends/ladder-rungs-1-2.md` | `span_metrics` not in `traces: exporters:` or not in `metrics: receivers:` |
| label present under a different name | 3 | `usePrometheusNaming` turned dots into underscores, or is off where the vocabulary expects underscores |
| metric label with thousands of values, `vm_hourly_series_limit_rows_dropped_total` rising | 1 | an id in an attribute the connector's `dimensions` lists, or on a metric the SDK emits; invariant 1 |
| VictoriaLogs `vl_streams_created_total` rising with every process | 2 | `VL-Stream-Fields` unset; every resource attribute is a stream field by default |
| trace split in two, root and CLIENT span have different `trace_id` | 1 | context not propagated across a thread, a process or an HTTP call; `core/context-propagation.md` |
| everything arrives late, or the last test of a run is missing | 1 | `BatchSpanProcessor` not flushed; call `shutdown_tracing` at exit; then 2 for `batch.timeout`; then 3 for `-search.latencyOffset` |
| numbers wrong after sampling | 2 | the connectors count only the spans the sampler kept; nothing scales them |
| every span has no `resource_attr:deployment.environment` | 2 | no `deployment.environment` on the resource; the `resource` processor did not insert it |
| store answers 400 with `json encoding isn't supported` | 2 | `encoding: json`, or an SDK exporter set to JSON |
| store answers 404 | 2 | the OTLP default path `/v1/<signal>` instead of the store's path |
| span never appears in VictoriaTraces and the resource has no `service.name` | 1 | the docs say every span **must** carry `service.name`; UNVERIFIED: whether it is dropped or stored under an empty stream |
| rate() on a delta counter draws garbage | 3 | delta temporality stored as is; use `sum_over_time` or add `delta_to_cumulative` |
| Grafana service dropdown empty, trace opens by id | 4 | the span is older than `-search.streamFieldsLookbehind`, default `72h` |

## Never

- Never start at rung 4. A blank chart says nothing about which hop failed.
- Never change two hops between two runs of the ladder.
- Never search by `name` alone. Names repeat; ids do not.
- Never conclude from VictoriaMetrics alone that the trace was lost. The
  span is in VictoriaTraces; the metric is a derivation of it.

## Stop and ask

- Rung 3 shows the span with the right fields and Grafana still shows
  nothing after the time picker, the data source URL and the tenant headers
  are checked. A version drift between VictoriaTraces and the Jaeger API
  Grafana expects; a person compares them.
- The span is at rung 2 with no export error and rung 3 has no log line at
  all. A network path between collector and store nobody described.

## Examples

| Observation | Verdict written |
| --- | --- |
| console shows the span, collector log shows it, LogsQL returns nothing, collector log has `404 Not Found` | `last seen: rung 2`, exporter path |
| console shows `sahara.cycle.id`, VictoriaTraces line has `span_attr:sahara.cycle.id` | `last seen: rung 4`, vocabulary spelling column updated |
| LogsQL returns the span, `traces_service_graph_request_total` returns nothing, `kind` was `1` | `last seen: rung 3`, span kind |
