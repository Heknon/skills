# MetricsQL, LogsQL and Jaeger queries to paste

Stamp: MetricsQL and URL examples for VictoriaMetrics v1.152.0, LogsQL for
VictoriaLogs v1.52.0, VictoriaTraces v0.11.1 querying docs, read
2026-09-17. Field names are the ones in `mapping.md`.

Rename before pasting: `sahara.cycle.id`, `sahara.entity.instance.id`,
`sahara.entity.definition`, `test.nodeid_hash`, the service name
`sahara-harness`, and every value in angle brackets. Metric labels assume
`-opentelemetry.usePrometheusNaming`, so they are `sahara_cycle_id`,
`service_name`, `span_name`. Log and span fields keep their dots.

Where each language goes:

- **LogsQL** at `curl http://<victoria-traces>:10428/select/logsql/query -d 'query=...'`
  for spans, at `http://<victorialogs>:9428/select/logsql/query` for logs,
  in vmui at `/select/vmui` on either, and in the VictoriaLogs data source.
- **Jaeger API** at `http://<victoria-traces>:10428/select/jaeger/api/...`
  and in Explore > Jaeger.
- **MetricsQL** at `curl http://<vmsingle>:8428/prometheus/api/v1/query -d 'query=...'`,
  in vmui at `/vmui`, and in the VictoriaMetrics data source.

## LogsQL rules that matter here

- `field:value` is a word match; `field:="value"` is the exact match. Use
  `:=` for ids.
- A field name with a dot works as is, `sahara.cycle.id:="c-1"`. Quote it
  when it holds `:` or a keyword: `"span_attr:sahara.cycle.id":="c-1"`.
  Quotes are `"`, `'` or backticks. "If in doubt, it is recommended quoting
  field names and filter args."
- `{field="value"}` is a stream filter and is the fast path. Only stream
  fields go inside the braces: `resource_attr:service.name` and `name` for
  spans, the `VL-Stream-Fields` set for logs.
- `_time:1h` limits time. Without it the whole retention is scanned.
- `field:""` selects entries where the field is empty or absent; `field:*`
  where it has any value.
- Pipes: `| fields a, b`, `| stats by (a) count() n`,
  `| stats quantile(0.95, duration) p95`, `| sort by (_time) desc`,
  `| limit 10`, `| stream_context before 5 after 5`, `| field_names`.
- Add `-d 'limit=100'` to `curl` or the response streams every match.

## All spans of one cycle

VictoriaTraces, LogsQL:

```
"span_attr:sahara.cycle.id":="<cycle id>" _time:24h | fields _time, trace_id, span_id, parent_span_id, name, kind, status_code, duration
```

Only the root spans, the tests:

```
"span_attr:sahara.cycle.id":="<cycle id>" parent_span_id:"" _time:24h | fields _time, trace_id, name, status_code, duration
```

Only the entity operations, kind `3` is `CLIENT`:

```
"span_attr:sahara.cycle.id":="<cycle id>" kind:="3" _time:24h | stats by ("span_attr:sahara.entity.definition", status_code) count() spans
```

Jaeger search, Explore > Jaeger > Search, `Tags` field:
`sahara.cycle.id=<cycle id>`. Resource attributes need the prefix:
`resource_attr:deployment.environment=ci`.

## All operations on one entity instance

```
"span_attr:sahara.entity.instance.id":="<instance id>" _time:7d | fields _time, trace_id, name, status_code, duration | sort by (_time)
```

Add the cycle when instance ids repeat: `AND "span_attr:sahara.cycle.id":="<cycle id>"`.

## Find one span by span id

```
span_id:="<16 hex characters>" _time:7d
```

The whole trace, any store that holds it:

```
trace_id:="<32 hex characters>" _time:7d | sort by (start_time_unix_nano)
```

Or `curl http://<victoria-traces>:10428/select/jaeger/api/traces/<32 hex characters>`.
Both ids are lowercase hex without `0x`.

## Documents where a label has an unexpected type

Every stored value is a string here, so a type mistake does not split a
field. It shows as a value with the wrong shape, or as an unexpected set of
label values. Check the shape:

```
"span_attr:sahara.retry.count":* AND NOT "span_attr:sahara.retry.count":~"^[0-9]+$" _time:24h | fields trace_id, "span_attr:sahara.retry.count"
```

Check which spellings of a key exist, a dotted and an underscored one at
once:

```
_time:24h | field_names
```

For metrics, list the values a label took today:

```sh
curl 'http://<vmsingle>:8428/prometheus/api/v1/label/sahara_entity_definition/values'
```

A run id that leaked into a label shows in the cardinality explorer as a
label with many unique values, or here:

```sh
curl 'http://<vmsingle>:8428/prometheus/api/v1/status/tsdb?topN=10&focusLabel=sahara_cycle_id'
```

## Spans that can become a dependency

Link 1 of chain A in `screens.md`: exit spans with a destination.

```
kind:in("3", "4") "span_attr:peer.service":* _time:1h | stats by ("span_attr:peer.service", "resource_attr:service.name") count() spans
```

The edges the connector actually wrote, link 4:

```
sum by (client, server, connection_type) (increase(traces_service_graph_request_total[1h]))
```

Zero rows there with spans above means the pair never met in one collector
within `store.ttl`, or the connector is missing. Unpaired spans:

```
sum by (client, server) (increase(traces_service_graph_unpaired_spans_total[1h]))
```

The VictoriaTraces graph, chain B:

```sh
curl 'http://<victoria-traces>:10428/select/jaeger/api/dependencies?endTs=<unix ms>&lookback=3600000'
```

## Error documents for a service

There are none. Errors are spans with `status_code` `2` and an `exception`
event:

```
{resource_attr:service.name="sahara-harness"} status_code:="2" _time:24h | fields _time, trace_id, name, status_message, "event:event_attr:exception.type:0", "event:event_attr:exception.message:0"
```

Group them:

```
{resource_attr:service.name="sahara-harness"} status_code:="2" _time:24h | stats by (name, "event:event_attr:exception.type:0") count() errors | sort by (errors) desc
```

Error share per span name from the connector, the RED "E". The
`status_code` value is `STATUS_CODE_ERROR` or `Error` depending on the
connector build; `collector.md` says how to read it once:

```
sum by (span_name) (rate(traces_span_metrics_calls_total{service_name="sahara-harness", status_code="STATUS_CODE_ERROR"}[5m]))
/
sum by (span_name) (rate(traces_span_metrics_calls_total{service_name="sahara-harness"}[5m]))
```

## Log lines for a trace id

VictoriaLogs:

```
trace_id:="<32 hex characters>" _time:7d | sort by (_time)
```

Lines outside any span carry no `trace_id`; find them by the correlation
key the logging filter adds:

```
"sahara.cycle.id":="<cycle id>" trace_id:"" _time:7d
```

Lines around one error in the same stream:

```
{service.name="sahara-harness"} severity_text:="Error" _time:1h | stream_context before 5 after 5
```

## Throughput, latency and p95 per span name

Requests per second of the test root spans:

```
sum by (span_name) (rate(traces_span_metrics_calls_total{service_name="sahara-harness", span_kind="SPAN_KIND_INTERNAL"}[5m]))
```

p95 duration in milliseconds, unit `ms` is the connector default:

```
histogram_quantile(0.95, sum by (span_name, le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="sahara-harness"}[5m])))
```

The same from spans directly, no connector, slower:

```
{resource_attr:service.name="sahara-harness"} parent_span_id:"" _time:1h | stats by (name) count() tests, quantile(0.95, duration) p95_ns
```

MetricsQL differences you will meet: `rate(x)` without `[d]` uses
`max(step, scrape_interval)`; `increase` counts the sample before the
window and is not extrapolated; rollups strip the metric name unless you
add `keep_metric_names`; `histogram_quantile` also takes `vmrange` buckets
from `histogram_over_time`, and `prometheus_buckets()` turns `vmrange` into
`le` for a heatmap; `count_values_over_time("label", q[d])` and
`label_match(q, "label", "regexp")` exist and PromQL lacks them.

## Never

- Never write `sahara.cycle.id` in a MetricsQL selector after choosing
  `usePrometheusNaming`.
- Never run a LogsQL query without `_time:` in production.
- Never search VictoriaTraces by `name` alone. Names repeat; ids do not.

## Stop and ask

- A query needs a field no row of `mapping.md` produces.
- A dotted label must be selected in MetricsQL. The syntax is UNVERIFIED.
