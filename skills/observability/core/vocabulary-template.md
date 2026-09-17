# Vocabulary template

Copy this file to the project as `vocabulary.md` and fill every section during
the Design task. Once filled it is the only source of names. Instrument tasks
read it; checkers read it. A name that is not here does not exist.

Rules for filling it in:

- Every entry is an exact string. No "something like", no examples in place of
  values.
- Every value has a type from `string`, `int`, `float`, `bool`.
- A label lists its allowed values. An attribute says `unbounded`.
- Keep the *Backend spelling* column current. It is what the index holds after
  the pipeline's renames, from `backends/<backend>/apm-server-mapping.md`.
- Change it only through a person. Record who and when at the bottom.

---

```markdown
# Vocabulary: <system name>

backend: <name and major version, from backends/README.md>
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
| deployment.environment | string | resource | service.environment | <rule> |
| <run level key> | string | every span, every log | labels.<spelling> | <rule> |
| <instance key> | string | every span, every log | labels.<spelling> | <rule> |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute (CLIENT and PRODUCER only) |
| --- | --- | --- | --- | --- |
| <noun.verb> | INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER | yes or no | <comma separated keys> | <peer.service or db.system or none> |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| <key> | string | label | a, b, c | labels.<spelling> |
| <key> | string | attribute | unbounded | labels.<spelling> |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| <name> | <span names> | <keys> |

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| <namespace.noun.measure> | counter, updowncounter, histogram, gauge | <UCUM unit> | <keys from the label tier only> | no, or the screen that shows it |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| <fixed sentence> | error, warning, info, debug | <keys> | yes or no |

## Forbidden

<values that must never appear in a name or a key, e.g. customer entity field names, nodeids, urls>

## Changes

| Date | Who | What |
| --- | --- | --- |
```
