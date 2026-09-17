# Correlation keys

**Verdict you produce:** the short list of attribute keys that every span,
every metric data point and every log line in this system carries, with their
exact names and types. It goes into `vocabulary.md` under *Correlation keys*.

Correlation is what lets a person walk from a metric spike to the traces under
it, from a trace to its log lines, and from a log line back to the unit of work
it happened in. It works only if the same key, with the same name and the same
value, is on all three signals. A key that is on spans but not on logs is a
dead end.

## Questions

1. **What identifies one deployment of this code?** Service name, service
   version, deployment environment. These are **resource attributes**, set once
   per process. Use the OpenTelemetry names: `service.name`,
   `service.version`, `deployment.environment`.
2. **What identifies one run or one tenant, above the unit of work?** A cycle,
   a job run, a customer. One key per level. These are **span attributes on
   every span** and **fields on every log line**. On metrics they are labels
   only if they pass `metrics/labels.md`; a run id does not.
3. **What identifies one occurrence of the unit of work?** The instance key
   from `core/unit-of-work.md`. On every span in the trace and every log line.
   Never a metric label.
4. **What identifies the place the work ran?** Worker id, host name, process
   id. `host.name` and `process.pid` are resource attributes. A logical worker
   id such as an xdist worker is a span attribute.
5. **Is the trace id enough for logs?** Yes for lines inside a span, and
   `logs/trace-correlation.md` injects it. No for lines outside any span, so
   those lines carry the keys from questions 2 and 4 by hand, from the same
   vocabulary module.

## Where each key lives

| Key | Resource | Span attribute | Log field | Metric label |
| --- | --- | --- | --- | --- |
| `service.name`, `service.version`, `deployment.environment` | yes | inherited | inherited | yes |
| `host.name`, `process.pid` | yes | inherited | inherited | no |
| run or tenant level ids | no | every span | every line | no |
| unit instance key | no | every span | every line | no |
| logical worker id | no | every span | every line | only if bounded |
| `trace.id`, `span.id` | no | implicit | injected | no, exemplars only |

Every backend rewrites some keys on the way in. Elastic rewrites dots to
underscores under `labels.*`, Prometheus style stores rewrite dots in metric
and label names, Tempo keeps dots and Loki keeps them only in structured
metadata. Read `backends/<backend>/mapping.md` before deciding on the
spelling, and record the stored spelling in the vocabulary beside the sent
one.

## Verdict

Write into the *Correlation keys* table of `vocabulary.md`, one row per key.
The *Where* cell is exactly one of `resource`, `every span`,
`every span except <names>`, `every log`, `every log inside a span`, or a span
clause and a log clause joined by a comma. `trace.id` and `span.id` get no
row; `logs/trace-correlation.md` injects them. A key that also passed
`metrics/labels.md` appears again in the *Labels* column of the *Metrics*
table, not here.

```
| <key> | string | <resource | every span | every span except <names> | every log | every log inside a span | <span clause>, <log clause>> | <stored spelling per backends/<backend>/mapping.md> | <value rule> |
```

For the running example the rows are `sahara.cycle.id`, `sahara.environment.id`
and `sahara.worker.id` with *Where* `every span, every log`, and
`test.nodeid_hash` with *Where* `every span except session.run, every log inside a span`.

## How they get onto everything

Not by hand. One module in the project holds the current values and:

- sets them as resource attributes at SDK startup,
- registers a `SpanProcessor` whose `on_start` copies the span-level keys onto
  every new span,
- installs a logging filter that copies the log-level keys onto every record.

`traces/recipes/python_otel_setup.py` and `logs/recipes/python_logging_setup.py`
do this. A call site never sets a correlation key.

## Never

- Never spell a key two ways. `cycle_id`, `cycle.id` and `cycleId` are three
  dead ends.
- Never put an instance id or a run id on a metric.
- Never rely on a person copying the key at each call site.
- Never make the service name carry a run id or a branch. The service is the
  code, not the run.

## Stop and ask

- The system has more than three levels above the unit of work. That many keys
  on every span is a cost; a person decides which levels matter.
- Two teams want different service names for the same process.
