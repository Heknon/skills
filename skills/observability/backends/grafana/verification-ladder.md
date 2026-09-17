# Verification ladder

Stamp: Tempo 3.0 API and troubleshooting docs, Loki 3.7 HTTP API and
request-validation docs, Prometheus 3.14 HTTP API, Mimir 3.2 HTTP API, Grafana
13.2 data source docs, opentelemetry-python 1.2x, grafana/tempo source at main
for reason labels, read 2026-09-17.

**Verdict you produce:** the number of the last rung where the span is seen,
1 to 4, and the first rung where it is missing or changed. Write it as
`last seen: rung N` at the top of your answer, then fix that hop only.

One span, pushed through every hop, bottom up. Do not skip a rung. A span
right at rung 2 and missing at rung 3 is a store problem, not an SDK one.
Rung 3 has three stores; check the one the missing thing lives in, and check
Tempo first because the other two are joined to it by ids Tempo holds.

Pick the span first. Use the harness's own unit of work: one test, so one
root span with at least one CLIENT span under it. Note the values you will
look for: `trace_id`, the root span's `span_id`, one attribute such as
`sahara.cycle.id`, and the CLIENT span's `peer.service`.

## Rungs 1 and 2: the SDK and the collector

Rungs 1 and 2 are the same on every backend and live in
`backends/ladder-rungs-1-2.md`. Run them first; start here only with the span
seen at rung 2, or at rung 1 when there is no collector.

## Rung 3: the stores

Ids here are lower case hex without `0x`. Every call below is `curl -s`, with
`-H 'X-Scope-OrgID: <tenant>'` added on a multi-tenant Loki or Mimir.

### Tempo

The trace by id, all blocks, no time window:

```sh
curl -s http://tempo:3200/api/v2/traces/4bf92f3577b34da6a3ce929d0e0e4736 | python3 -m json.tool | head -80
```

HTTP 404 means no block holds it. HTTP 200 returns OpenTelemetry JSON: a
resource with `service.name`, spans with `traceId`, `spanId`, `parentSpanId`,
`name`, `kind` such as `SPAN_KIND_CLIENT`, `attributes` as `{key, value:
{stringValue}}` pairs with the dotted keys intact, and `status.code`.
UNVERIFIED: the exact wrapper field names of the v2 body; `/api/traces/<id>`
returns the same spans under `batches`. Check: the CLIENT span's
`parentSpanId` equals the root's `spanId`; `sahara.cycle.id` is a string
attribute; `peer.service` is present.

The same by search, which proves the attribute is queryable, not just stored:

```sh
curl -s -G http://tempo:3200/api/search \
  --data-urlencode 'q={ span.sahara.cycle.id = "c-2026-09-17-01" && span:name = "tests/test_one.py::test_create" }' \
  --data-urlencode 'start=<unix seconds>' --data-urlencode 'end=<unix seconds>'
```

The body is `traces[]` with `traceID`, `rootServiceName`, `rootTraceName`,
`startTimeUnixNano`, `durationMs`, `spanSets[].spans[].spanID`. An empty
`traces` with a 200 from the trace-by-id call is a query problem: wrong
scope, a quoted number, or the window. `tempo-cli query api search
tempo:3200 '{ span.sahara.cycle.id = "c-2026-09-17-01" }' now-1h now` runs
the same search.

When nothing arrives, Tempo's own metrics on `:3200/metrics` are the witness:
`tempo_distributor_spans_received_total` rises when the collector reached it;
`tempo_discarded_spans_total{reason="trace_too_large"|"live_traces_exceeded"|"rate_limited"}`
names the refusal, source: `modules/overrides/discarded_spans.go`;
`tempo_receiver_refused_spans` counts what the receiver itself refused. Turn
on `distributor.log_discarded_spans.enabled: true` to see each refused span
in the log with its trace id.

### Prometheus or Mimir, the derived series

Two `collection_interval`s after the span, default `15s`, plus remote write:

```sh
curl -s -G http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=traces_spanmetrics_calls_total{service="sahara-harness", span_name="tests/test_one.py::test_create"}'
curl -s -G http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=traces_service_graph_request_total{client="sahara-harness", server="tank"}'
```

On Mimir the path is `:8080/prometheus/api/v1/query`. The body is
`data.resultType: vector` and `data.result[]` with `metric` and `value`. An
empty `result` for the first query with the span in Tempo means the
`span-metrics` processor is off, the generator's `remote_write` fails, or
`max_active_series` was hit; read `tempo_metrics_generator_spans_received_total`,
`tempo_metrics_generator_registry_series_limited_total` and
`prometheus_remote_storage_samples_failed_total` on Tempo's `/metrics`. An
empty `result` for the second with the first present means the span was not
`CLIENT`, had no `peer.service`, or `service-graphs` is off. Under the
`collector connectors` verdict the names are `traces_span_metrics_calls_total`
and the label `service_name`.

Your own metric, one export interval after the process flushed:

```sh
curl -s -G http://prometheus:9090/api/v1/query --data-urlencode 'query=sahara_controller_polls_total'
```

Nothing, and the collector shows the metric at rung 2: the name is spelled
per `mapping.md`, `_total` and the unit appended; `--web.enable-otlp-receiver`
is set, check `GET :9090/api/v1/status/flags`; the temporality is cumulative.

### Loki

```sh
curl -s -G http://loki:3100/loki/api/v1/query_range \
  -H 'X-Scope-OrgID: <tenant>' \
  --data-urlencode 'query={service_name="sahara-harness"} | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"' \
  --data-urlencode 'limit=20'
```

The body is `data.resultType: streams`, `data.result[].stream` with the
index labels, and `values[]` of `[<ns timestamp>, <line>, {<structured
metadata>}]`. Check: `stream.service_name` is the service; the metadata
object has `trace_id`, `span_id`, `severity_text`, `sahara_cycle_id` with
underscores. No stream at all: `GET :3100/loki/api/v1/labels` must list
`service_name`; if it lists nothing for the range, the push was refused, and
`loki_discarded_samples_total{reason=...}` on `:3100/metrics` names why.

## Rung 4: Grafana

Explore, Tempo data source, **TraceQL** tab:

```
{ trace:id = "4bf92f3577b34da6a3ce929d0e0e4736" }
```

Open the trace. The CLIENT span sits under the root; its details show the
dotted attributes. Click the logs icon on the span: the split shows the Loki
lines from rung 3, or it shows the LogQL it built, which is the fastest way
to see a `service.name` tag that should have been `service_name`. Switch to
the **Service Graph** query type: the node `sahara-harness` has an edge to
`tank`; the table below lists the span name once `SPAN_KIND_SERVER` is not
the filter. Grafana shows only what rung 3 holds. A span in rung 3 and absent
here is a time picker, a data source uid in `serviceMap` or
`tracesToLogsV2`, or a tag mapping, never lost data.

## Symptom to rung

| Symptom | First rung to check | Usual cause |
| --- | --- | --- |
| root span missing entirely | 1 | span never ended, or process exited before `force_flush`; then 3, `tempo_discarded_spans_total` |
| span present, no edge on the service graph | 3, the second PromQL | not `SpanKind.CLIENT`, or no `peer.service`, or `service-graphs` off, or under two intervals old |
| attribute present under a different name | 3 | Loki and Prometheus underscored the key; Tempo did not. The vocabulary's spelling column is stale, see `mapping.md` |
| TraceQL `=` finds the span and `>` does not, or the reverse | 1 | the value is a string in one place and a number in another; invariant 7 |
| Loki HTTP 400 with `reason` in `loki_discarded_samples_total` | 3 | `structured_metadata_too_many`, `label_name_too_long`, `too_far_behind`; the reason names the limit in `collector.md` |
| trace split in two, root and CLIENT span have different `trace_id` | 1 | context not propagated across a thread, a process or an HTTP call; `core/context-propagation.md` |
| everything arrives late, or the last test of a run is missing | 1 | `BatchSpanProcessor` not flushed; call `shutdown_tracing` at exit; then 2 for `batch.timeout` |
| numbers wrong after sampling | 3 | a sampler before Tempo with the generator on; counts follow the sampled set; `overview.md` decision rule |
| every log stream lacks the environment | 2 | the resource carries `deployment.environment`, Loki indexes `deployment.environment.name`; promote or rename in the vocabulary |
| Loki refuses with `stream_limit` or Prometheus series count jumps | 1 | an id became a Loki index label or a `dimensions` entry; invariant 11 |
| trace found by id, search returns nothing | 3 | window outside `start`/`end`; `span.` used for a resource key; a number quoted |
| span metrics series exist, table in Service Graph empty | 4 | default filter `span_kind="SPAN_KIND_SERVER"`; or the series are `traces_span_metrics_*` from the collector |
| service graph works, `Logs for this span` empty | 4 | `tracesToLogsV2.tags` maps `service.name` to nothing; logs carry no `trace_id`; time shift too narrow |
| exemplars toggle shows nothing | 3 | `--enable-feature=exemplar-storage` missing, or `send_exemplars` false on the generator's `remote_write` |
| generator series stop growing at a round number | 3 | `max_active_series` hit; `tempo_metrics_generator_registry_series_limited_total` rises |
| emitted metric arrives, its resource attributes do not | 3 | they are on `target_info`; promote with `otlp.promote_resource_attributes` or join by `job`, `instance` |
| metric name has a suffix nobody wrote | 3 | `UnderscoreEscapingWithSuffixes` added the unit and `_total`; that is the spelling, update the vocabulary |
| counter never rises, or Prometheus logs dropped delta | 1 | SDK on delta temporality; set cumulative |
| TraceQL metrics query errors on Tempo 2.x | 3 | `local-blocks` not in the processors list; `overview.md` |
| every Loki stream is `service_name="unknown_service"` | 1 | no `service.name` on the log exporter's resource |

## Never

- Never start at rung 4. A blank panel says nothing about which hop failed.
- Never change two hops between two runs of the ladder.
- Never search by span name alone. Names repeat; ids do not.
- Never conclude from an empty Prometheus result that the span is missing.
  Prometheus holds counts of spans, never spans.

## Stop and ask

- Rung 3 shows the trace, the series and the log line, and Grafana shows
  nothing after the time picker and the data source uids are checked. A
  person compares the Grafana version with the data source plugin.
- The span is at rung 2 with the right exporter and Tempo's
  `tempo_distributor_spans_received_total` never moves. A network path
  between collector and Tempo nobody described.

## Examples

| Observation | Verdict written |
| --- | --- |
| console shows the span, collector log shows it, `/api/v2/traces` returns 404, `tempo_discarded_spans_total{reason="trace_too_large"}` rose | `last seen: rung 2`, `max_bytes_per_trace` |
| console shows `sahara.cycle.id`, Loki metadata has `sahara_cycle_id` | `last seen: rung 4`, vocabulary spelling column updated |
| trace in Tempo, `traces_service_graph_request_total` empty, `kind` was `INTERNAL` | `last seen: rung 3`, span kind |
