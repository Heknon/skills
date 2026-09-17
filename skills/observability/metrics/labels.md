# Metric labels

**Verdict you produce:** for each metric, the exact list of attribute keys
passed with every measurement, the allowed values of each, and the number of
time series the metric will make. It goes into the *Labels* column of the
*Metrics* table in `vocabulary.md`.

Every distinct combination of label values is a separate time series, kept for
the life of the index and exported again every interval. A metric label is the
strictest tier there is. It comes only from the **label** tier of
`core/naming-and-cardinality.md`. Nothing from the attribute tier is ever a
metric label, however useful it looks.

## Questions

For each key you want to pass with a measurement:

1. **Is the key in the *Span attributes* table of `vocabulary.md` with tier
   `label`?** No: it is not a metric label. Do not add it. If you need it,
   stop and ask.
2. **Is the value the same for the whole process?** `service.name`,
   `service.version`, `deployment.environment`, `host.name`. Yes: it is a
   resource attribute already on every metric. Do not pass it again.
3. **Is it an id, a run id, a hash, a timestamp, a path, a nodeid, or a
   parameter value?** Yes: never a label. It goes on spans and logs as an
   attribute, and a person reaches the metric's traces through
   `service.name` and the time range.
4. **Is it a worker id?** It may be a label only if the vocabulary lists every
   value, such as `gw0` to `gw7`. A worker id that grows with the machine
   count is not a label.
5. **Is the value chosen by a customer or read from input?** Yes: never a
   label, never a key. Invariant 11.
6. **Multiply the allowed value counts of every key that passed.** That is
   the series count for this metric. Over 1000: stop and ask. The SDK's
   default cardinality limit is 2000 distinct attribute sets per instrument
   per collection cycle; past it the spec folds measurements into an
   overflow series. UNVERIFIED: whether opentelemetry-python 1.2x enforces
   that limit by default.

## Estimating the series count

```
series = product over labels of (number of allowed values)
documents per interval per process = number of distinct label sets actually seen
```

| Metric | Labels and sizes | Series |
| --- | --- | --- |
| `sahara.controller.polls` | `entity.definition` 40, `entity.operation` 5, `outcome` 2 | 400 |
| `sahara.entities.live` | `entity.definition` 40 | 40 |
| `sahara.worker.queue.depth` | `worker.id` 8 | 8 |
| `sahara.controller.polls` with `entity.id` | unbounded | refused |

## How Elastic 8.x stores them

Source: `elastic/apm-data` `input/otlp/metrics.go` and `metadata.go`, and the
APM index templates in the Elasticsearch `apm-data` plugin.

- A string or bool attribute becomes `labels.<key>`, mapped `keyword`. A bool
  is stored as the string `true` or `false`.
- An int or double attribute becomes `numeric_labels.<key>`, mapped
  `scaled_float` with `scaling_factor: 1000000`. That is a different field
  from `labels.<key>`. Send every label as a string, always. Invariant 7.
- Span and log attribute keys have dots rewritten to underscores before they
  become labels: `entity.definition` is `labels.entity_definition`. For metric
  data point attributes `metrics.go` passes the key to `setLabel` unchanged.
  UNVERIFIED: whether a metric label reaches the index as
  `labels.entity.definition` or `labels.entity_definition`. Look at one
  document in Discover under `metrics-apm.app.*` and write what you see into
  the *Backend spelling* column. Until then, filter on both.
- One document is written per distinct attribute set per timestamp, holding
  every metric that shares that set. More label sets means more documents,
  not wider ones.
- Each distinct label key is a mapped field. The index field limit is
  `index.mapping.total_fields.limit`, default `1000`. The APM settings
  component template sets `index.mapping.total_fields.ignore_dynamic_beyond_limit: true`,
  so a key past the limit is stored but not indexed, and a filter on it
  returns nothing, silently. UNVERIFIED: the same setting on 8.x installations
  whose templates come from the Fleet APM integration rather than the
  Elasticsearch `apm-data` plugin.
- `metrics-apm.app.*` is not a time series data stream: its index template
  sets no `index.mode: time_series` and no `time_series_dimension`. Labels are
  ordinary keyword fields, not TSDB dimensions. UNVERIFIED for 8.x versions
  before the `apm-data` plugin owned the templates.

## Verdict

Write into the *Metrics* table, *Labels* column, and make sure each key has a
row in *Span attributes* with tier `label` and its allowed values:

```
| <metric name> | ... | <unit> | entity.definition, entity.operation, outcome | no |
```

## Never

- Never pass a value that is not in the vocabulary's allowed list. The
  recipe's `label_set` raises on one; keep it that way.
- Never pass a number as a label. `worker.id="3"`, not `3`.
- Never pass the correlation keys `cycle.id`, `environment.id` or the unit
  instance key on a metric. They are attributes on spans and fields on logs.
- Never pass the same key with different spellings in different places.
- Never let a label set be built from a dictionary you did not write.

## Stop and ask

- A person wants to group a chart by something with more than a few hundred
  values. That is a cost decision.
- A key you need is not in the vocabulary. Name it and ask.
- The series estimate is over 1000 for one metric.

## Examples

| Key | Tier in vocabulary | Metric label | Why |
| --- | --- | --- | --- |
| `entity.definition` | label, 40 values | yes | bounded, listed, grouped on charts |
| `entity.operation` | label, 5 values | yes | fixed verb list |
| `outcome` | label, `success` `failure` | yes | two values |
| `worker.id` | label, `gw0` to `gw7` | yes | bounded by the vocabulary |
| `entity.id` | attribute | no | one per instance |
| `cycle.id` | correlation key | no | one per run |
| `test.nodeid_hash` | instance key | no | one per test |
| entity field names from a customer definition | forbidden | no | customer controlled keys |
