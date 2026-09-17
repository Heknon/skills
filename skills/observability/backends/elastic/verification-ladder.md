# Verification ladder

Stamp: Elastic 8.17 to 8.19, opentelemetry-python 1.2x, read 2026-09-17.

**Verdict you produce:** the number of the last rung where the span is seen,
1 to 4, and the first rung where it is missing or changed. Write it as
`last seen: rung N` at the top of your answer, then fix that hop only.

One span, pushed through every hop, bottom up. Do not skip a rung. A span
right at rung 2 and missing at rung 3 is an APM Server problem, not an SDK one.

Pick the span first. Use the harness's own unit of work: one test, so one
transaction with at least one CLIENT span under it. Note the values you will
look for: `trace.id`, the root span's `span.id`, one label key such as
`cycle.id`, and the CLIENT span's `peer.service`.

## Rung 1: the SDK

Prove the span exists in the process before anything leaves it.

```sh
TRACE_CONSOLE_EXPORT=1 python -m pytest tests/test_one.py -q 2>&1 | grep -A40 '"name":'
```

`traces/recipes/python_otel_setup.py` reads `TRACE_CONSOLE_EXPORT=1` and adds
`ConsoleSpanExporter` next to the OTLP exporter. `traces/recipes/python_file_exporter.py`
writes the same JSON to a file instead when stdout is noisy. One JSON object
per span, in the shape of `ReadableSpan.to_json()`:

```json
{
  "name": "tests/test_one.py::test_create",
  "context": {"trace_id": "0x...", "span_id": "0x...", "trace_state": "[]"},
  "kind": "SpanKind.INTERNAL",
  "parent_id": null,
  "status": {"status_code": "UNSET"},
  "attributes": {"cycle.id": "c-2026-09-17-01", "environment.id": "env-3", "test.nodeid_hash": "..."},
  "resource": {"attributes": {"service.name": "sahara-harness", "deployment.environment": "ci"}}
}
```

Check, per span: `name` is the vocabulary's string with the varying part
removed; `kind` is `SpanKind.CLIENT` on the entity operation; `parent_id` of
the CLIENT span is the test span's `span_id`; every correlation key is in
`attributes` as a string; `status.status_code` is `ERROR` when the test
failed; `resource.attributes` has `service.name`. A span missing here is not
created, not ended, or exported before `force_flush` ran. Fix at the call
site. Nothing downstream can add what is missing here.

## Rung 2: the collector

Skip when there is no collector. Otherwise the `debug` exporter from
`collector.md` prints every span it forwards, on stderr:

```sh
otelcol-contrib --config config.yaml 2>&1 | grep -B2 -A30 'Name           : tests/test_one.py::test_create'
```

Expected:

```
info    Traces  {"otelcol.component.id": "debug", "otelcol.component.kind": "Exporter", "otelcol.signal": "traces", "resource spans": 1, "spans": 2}
ResourceSpans #0
Resource attributes:
     -> service.name: Str(sahara-harness)
     -> deployment.environment: Str(ci)
ScopeSpans #0
Span #0
    Trace ID       : 4bf92f3577b34da6a3ce929d0e0e4736
    Parent ID      :
    ID             : 00f067aa0ba902b7
    Name           : tests/test_one.py::test_create
    Kind           : Internal
Attributes:
     -> cycle.id: Str(c-2026-09-17-01)
```

What changed against rung 1: ids are printed without `0x`; `kind` is
`Internal`, `Client`; a key you configured `delete` for is gone; a key you
configured `hash` for is 40 hex characters; `deployment.environment` appears
in **Resource attributes** if the `resource` processor inserted it. Anything
else that differs is a processor you forgot to write into the vocabulary.
Keys are still dotted here. Nothing under `labels` yet.

`grep -i 'exporting failed' collector.log` must print nothing; if it does,
`collector.md` has the line and its cause.

## Rung 3: APM Server and Elasticsearch

Kibana **Dev Tools**, or `curl -u <user> -H 'Content-Type: application/json'`
against the same paths. Ids here are lower case hex without `0x`.

```
GET traces-apm*/_search
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"trace.id": "4bf92f3577b34da6a3ce929d0e0e4736"}}
      ]
    }
  },
  "sort": [{"@timestamp": "asc"}],
  "size": 50
}
```

For one document use `{"term": {"transaction.id": "00f067aa0ba902b7"}}` for
the root and `{"term": {"span.id": "..."}}` for the CLIENT span. The spellings
are the ones in `apm-server-mapping.md`; check these fields in `_source`:

- root: `processor.event: transaction`, `transaction.name` equal to the span
  name, `transaction.type`, `event.outcome: success|failure|unknown`,
  `service.environment` equal to `deployment.environment`,
  `labels.cycle_id`, `labels.environment_id`, `labels.test_nodeid_hash`.
  Dotted keys are now underscored under `labels.*`; numbers went to
  `numeric_labels.*` instead.
- CLIENT span: `processor.event: span`, `span.name`, `span.subtype`,
  `span.destination.service.resource` equal to `peer.service`,
  `parent.id` equal to the root's `transaction.id`.

Dependency metrics are aggregated on a `1m` interval; wait two minutes, then:

```
GET metrics-apm.service_destination*/_search
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"metricset.name": "service_destination"}},
        {"term": {"service.name": "sahara-harness"}},
        {"term": {"span.destination.service.resource": "tank"}},
        {"range": {"@timestamp": {"gte": "now-15m"}}}
      ]
    }
  },
  "size": 5
}
```

A hit carries `span.destination.service.response_time.count` and
`span.destination.service.response_time.sum.us`. No hit with the span present
means the span had no `peer.service` or was not `SpanKind.CLIENT`.

When nothing arrives, APM Server's log is the witness. In Kibana **Fleet** >
the agent > **Logs** > dataset `elastic_agent.apm_server`, or the ndjson file
from `elastic-agent.md`. Look for `authentication failed`,
`request body too large`, `Limit of total fields [1000] in [INDEX_NAME] has
been exceeded`, and `mapper_parsing_exception`. `UNVERIFIED:` exact wording of
the too-large event line.

## Rung 4: Kibana

The screen names and menu paths are in `kibana-screens.md`. For this ladder:
the service's **Transactions** tab lists `transaction.name`, and the trace
explorer takes KQL. Narrow to the one span with:

```
trace.id : "4bf92f3577b34da6a3ce929d0e0e4736"
```

or `labels.cycle_id : "c-2026-09-17-01" and transaction.name : "tests/test_one.py::test_create"`.
The waterfall must show the CLIENT span under the transaction and the
service's **Dependencies** tab must list the `peer.service` value once the
metrics from rung 3 exist. Kibana shows only what rung 3 holds. A span in
rung 3 and absent here is a time picker, an environment selector, or a
sampling rate, never lost data.

## Symptom to rung

| Symptom | First rung to check | Usual cause |
| --- | --- | --- |
| transaction missing entirely | 1 | span never ended, or process exited before `force_flush`; then 3 for `Unauthenticated` |
| span present, no dependency row | 3, the metrics query | not `SpanKind.CLIENT`, or no `peer.service`, or under two minutes old |
| label present under a different name | 3 | dotted key underscored to `labels.<a_b>`; the vocabulary's spelling column is stale, see `apm-server-mapping.md` |
| label present in `labels.*` on one doc and `numeric_labels.*` on another | 1 | the value is a string in one place and a number in another; invariant 7 |
| document rejected, `mapper_parsing_exception`, `failed to parse field [<field>] of type [<type>] in document with id` | 3 | a value of a second type on a field the index already mapped; usually a log field or an object sent as an attribute |
| trace split in two, root and CLIENT span have different `trace.id` | 1 | context not propagated across a thread, a process or an HTTP call; `core/context-propagation.md` |
| everything arrives late, or the last test of a run is missing | 1 | `BatchSpanProcessor` not flushed; call `shutdown_tracing` at exit; then 2 for `batch.timeout` |
| numbers wrong after sampling | 3 | head sampling without a consistent probability sampler, or tail sampling that saw half a trace; counts follow the sampled set |
| every span has `service.environment` unset | 2 | no `deployment.environment` on the resource; the `resource` processor did not insert it |
| `Limit of total fields [1000]` in APM Server log | 1 | a customer-controlled key became an attribute key; invariant 11 |

## Never

- Never start at rung 4. A blank chart says nothing about which hop failed.
- Never change two hops between two runs of the ladder.
- Never search by `span.name` alone. Names repeat; ids do not.

## Stop and ask

- Rung 3 shows the document with the right fields and Kibana still shows
  nothing after the time picker and environment are checked. Version drift
  between the integration and Kibana; a person compares them.
- The span is at rung 2 with the right header and rung 3 has no log line at
  all. A network path between collector and APM Server nobody described.

## Examples

| Observation | Verdict written |
| --- | --- |
| console shows the span, collector log shows it, `_search` returns 0 hits, log has `authentication failed` | `last seen: rung 2`, token |
| console shows `cycle.id`, `_source` has `labels.cycle_id` | `last seen: rung 4`, vocabulary spelling column updated |
| `_search` returns the span, `service_destination` returns 0 hits, `kind` was `INTERNAL` | `last seen: rung 3`, span kind |
