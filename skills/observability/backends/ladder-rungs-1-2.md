# Verification ladder, rungs 1 and 2

Stamp: opentelemetry-python 1.2x, opentelemetry-collector-contrib `debug`
exporter output at main, read 2026-09-17.

The first two rungs are the same on every backend: the SDK and the collector
do not know which store is behind them. Every `backends/<backend>/verification-ladder.md`
starts at rung 3 and sends you here first. Come back to it with the number of
the last rung where the span was seen, and continue there.

Pick the span first, as that ladder says: one test, so one root span with at
least one CLIENT span under it, and note the `trace_id`, the root's `span_id`,
`sahara.cycle.id` and the CLIENT span's `peer.service`.

## Rung 1: the SDK

Prove the span exists in the process before anything leaves it.

```sh
TRACE_CONSOLE_EXPORT=1 python -m pytest tests/test_one.py -q 2>&1 | grep -A40 '"name":'
```

`traces/recipes/python_otel_setup.py` reads `TRACE_CONSOLE_EXPORT=1` and adds
`ConsoleSpanExporter` next to the OTLP exporter. When stdout is noisy, use
`traces/recipes/python_file_exporter.py` instead; it writes one JSON object per
span to `TRACE_EXPORT_FILE` in the checker's own shape, which is documented at
the bottom of that recipe and is what `checks/check_spans.py` reads directly.
The console exporter prints one JSON object per span in the shape of
`ReadableSpan.to_json()`, which the checker also accepts:

```json
{
  "name": "tests/test_one.py::test_create",
  "context": {"trace_id": "0x...", "span_id": "0x...", "trace_state": "[]"},
  "kind": "SpanKind.INTERNAL",
  "parent_id": null,
  "status": {"status_code": "OK"},
  "attributes": {"sahara.cycle.id": "c-2026-09-17-01", "sahara.environment.id": "env-3", "sahara.worker.id": "gw0", "test.nodeid_hash": "..."},
  "resource": {"attributes": {"service.name": "sahara-harness", "deployment.environment": "ci"}}
}
```

The file exporter's shape for the same span carries the ids without `0x`,
`"kind": "INTERNAL"`, `"parent_span_id": null`, `"status": {"code": "OK"}`,
and the same `attributes` and `resource` keys.

Check, per span: `name` is the vocabulary's string with the varying part
removed; `kind` is `SpanKind.CLIENT` on the entity operation; `parent_id` of
the CLIENT span is the test span's `span_id`; every correlation key is in
`attributes` as a string; `status.status_code` is `OK` when the test passed
and `ERROR` when it failed; `resource.attributes` has `service.name` and
`deployment.environment`. A span missing here is not created, not ended, or
exported before `force_flush` ran. Fix at the call site. Nothing downstream
can add what is missing here.

## Rung 2: the collector

Skip when there is no collector. Otherwise the `debug` exporter from the
backend's `collector.md` prints every span it forwards, on stderr:

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
     -> sahara.cycle.id: Str(c-2026-09-17-01)
```

What changed against rung 1: ids are printed without `0x`; `kind` is
`Internal`, `Client`; a key you configured `delete` for is gone; a key you
configured `hash` for is 40 hex characters; a resource key appears in
**Resource attributes** if the `resource` processor inserted it. Anything
else that differs is a processor you forgot to write into the vocabulary.
Keys are still dotted here. The store's spelling, underscores under
`labels.*` on Elastic, underscores in Loki and Prometheus, `span_attr:`
prefixes in VictoriaTraces, is applied at rung 3 and is in the backend's
`mapping.md`.

`grep -i 'exporting failed' collector.log` must print nothing; if it does, the
backend's `collector.md` has the line and its cause. With one exporter per
store, a line that names one exporter means only that store is unreached;
the others may be fine.

Two more things to read here when the config has them:

- One `info Traces|Metrics|Logs` line per signal per batch. A signal whose
  line never appears is not in a pipeline that has `debug`.
- Connectors in the traces pipeline: the same `debug` exporter prints the
  metrics they made, about `metrics_flush_interval` later, as `Metric #0`
  with `-> Name: traces.span.metrics.calls` and data points carrying
  `span.name: Str(tests/test_one.py::test_create)`. No such block within two
  flush intervals means the connector is not wired into the traces pipeline.

Then the collector's own counters at `http://127.0.0.1:8888/metrics`:
`otelcol_exporter_sent_spans`, `otelcol_exporter_send_failed_spans`,
`otelcol_exporter_sent_metric_points`, `otelcol_exporter_sent_log_records`,
`otelcol_receiver_refused_spans`. A `send_failed` that moves is rung 3.

## Never

- Never start at rung 3. A span the collector never printed is not a store
  problem.
- Never change two hops between two runs of the ladder.
