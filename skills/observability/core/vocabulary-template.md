# Vocabulary template

Copy this file to the project as `vocabulary.md` and fill every section during
the Design task. Once filled it is the only source of names. Instrument tasks
read it; checkers read it. A name that is not here does not exist.

Rules for filling it in:

- Every entry is an exact string. No "something like", no examples in place of
  values. A span name that is a rule, such as a test's nodeid, is written as a
  glob, `tests/*::test_*`, never as a `<placeholder>`.
- Every value has a type from `string`, `int`, `float`, `bool`.
- A label lists its allowed values. An attribute says `unbounded`.
- The *Where* cell of a correlation key is exactly one of `resource`,
  `every span`, `every span except <names>`, `every log`,
  `every log inside a span`, or a span clause and a log clause joined by a
  comma, such as `every span except session.run, every log inside a span`.
- An *Instrument* cell is one bare word: `counter`, `updowncounter`,
  `histogram`, `gauge`, or `none` when the backend derives the metric.
  Synchronous or observable goes in the note under the table, not in the cell.
- A *Level* cell is one of `error, warn, info, debug`, lower case. The shipped
  value is the upper case word, `ERROR, WARN, INFO, DEBUG`.
- Keep the *Backend spelling* column current. It is what the index holds after
  the pipeline's renames, from `backends/<backend>/mapping.md`.
- The checkers read the tables under *Correlation keys*, *Spans*, *Span
  attributes*, *Span events*, *Metrics* and *Logs* by their column headers.
  Keep the headers as they are here. The other sections are read by people.
- Change it only through a person. Record who and when at the bottom.

---

```markdown
# Vocabulary: <system name>

backend: <name and major version, from backends/README.md>
collector: <version, or none>
verified against: <backend version> on <date>

## Unit of work

unit: <noun>
root span name: <exact rule, e.g. "nodeid with the parametrization removed">
instance key: <attribute key>
outer roots: <list, or none>

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | <rule> |
| service.version | string | resource | service.version | <rule> |
| deployment.environment | string | resource | <stored spelling per backends/<backend>/mapping.md> | <rule> |
| <run level key> | string | every span, every log | <stored spelling per backends/<backend>/mapping.md> | <rule> |
| <instance key> | string | every span except <outer root names>, every log inside a span | <stored spelling per backends/<backend>/mapping.md> | <rule> |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute | Fails when |
| --- | --- | --- | --- | --- | --- |
| <noun.verb, or a glob for a root span rule> | INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER | yes or no | <comma separated attribute keys> | <peer.service or db.system for CLIENT and PRODUCER; none otherwise> | <exact condition> ; expected: <conditions that stay OK, or none> |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| <key> | string | label | a, b, c | <stored spelling> |
| <key> | string | attribute | unbounded | <stored spelling> |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| <name> | <span names> | <keys> |

## Links

| From span | To span | link.relation |
| --- | --- | --- |
| <span name> | <span name> | belongs_to, operates_on, produced_by, retries |

## Boundaries

| From -> To | Verdict | Carrier | Far side |
| --- | --- | --- | --- |
| <from> -> <to> | automatic, inject and extract, or link by key | <header, TRACEPARENT environment variable, message attribute, or key name> | child or link |

## Long lived things

thing: <noun>
verdict: own linked root span | inferred from attributes
identity key: <attribute key>, on every span that touches it
root span name: <name, or none>
kept apart by: <label attribute key and value from the Span attributes table, or none>
opened at / closed at: <hook or call pair, or none>
linked from: <which spans carry a Link to it, or none>

## Lanes and time

lane: host.name + process.pid, resource attributes
worker key: <span attribute key, e.g. sahara.worker.id> = <value rule, e.g. PYTEST_XDIST_WORKER>
host metrics emitted by: <collector hostmetrics receiver on each host | the process named here>
clock source: <ntp or chrony, and the command that shows it>
compare timestamps: within one lane only; across lanes by structure
cross process spans: none; hand offs are two spans joined by a Link and <key>

## Metrics

temporality: <cumulative | delta, from backends/README.md>
span metrics derived by: <APM Server | Tempo metrics-generator | collector connectors | nothing, from backends/README.md>

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| <namespace.noun.measure> | counter, updowncounter, histogram, gauge, or none | <UCUM unit> | <keys from the label tier only, or (none)> | no, or "yes, derived: see backends/<backend>/screens.md" |

observable instruments: <metric names whose value comes from a callback, or none>

## Volume

sampler: <parentbased_always_on | parentbased_traceidratio rate=<r> | tail: collector | tail: backend> ; derived counts exact: <yes | low by 1/r>
span limits: OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=<n>, OTEL_SPAN_EVENT_COUNT_LIMIT=<n>, others default
large values: <attribute key> as JSON string ; <attribute key> as locator, stored at <where>
histogram boundaries: <metric name>: <upper bounds in the metric's unit> ; ...
retention: traces <days>, metrics <days>, logs <days> ; questions past trace retention: <metric names>

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| <fixed sentence> | error, warn, info, debug | <keys> | yes or no |

## Forbidden

<values that must never appear in a name or a key, e.g. customer entity field names, nodeids, urls>

## Changes

| Date | Who | What |
| --- | --- | --- |
| <date> | <who> | <metric>: question "<sentence>", pattern <name>, recorded <moment>, combine <sum|max|per process> |
```
