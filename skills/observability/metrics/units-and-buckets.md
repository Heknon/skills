# Units and buckets

**Verdict you produce:** for every metric the exact UCUM unit string passed to
the instrument, and for every histogram the exact boundary list and the View
that installs it. Both go into `vocabulary.md`, the unit in the *Metrics* table
and the boundaries as a `histogram boundaries:` line in the `## Volume`
section, together with the temporality this installation uses.

## Units

The unit is the `unit=` argument of the instrument. It is never part of the
name. Semantic conventions: "Units do not need to be specified in the names
since they are included during instrument creation."

| Measures | Unit string | Never |
| --- | --- | --- |
| duration | `s` | `ms`, `us`, `_seconds` in the name |
| size | `By` | `KiBy`, `MB`, `_bytes` in the name |
| ratio, fraction of a total | `1` | `%` |
| count of a thing | `{thing}` in the singular, such as `{test}`, `{poll}`, `{entity}` | a bare `1` for a count |

Rules, from the OpenTelemetry semantic conventions on metrics:

1. Base units. Seconds, not milliseconds. Bytes, not kibibytes. Record
   `0.005`, not `5`.
2. UCUM strings. A count annotation is in braces and must match the
   grammatical number of what it counts.
3. Names are not pluralized "unless the value being recorded represents
   discrete instances of a countable quantity", and then the unit is an
   annotation like `{operation}`.
4. Do not count on the backend storing the unit; whether it does is in
   `backends/<backend>/mapping.md`. Elastic 8.x APM Server does not:
   `metrics.go` carries the comment `TODO(axw) support units`, and the field
   is a bare number. The vocabulary is the only record of the unit. Put it in
   the description too: `description="Poll round trip time in seconds"`.

## Histogram boundaries

The SDK default boundaries are
`(0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000)`.
They were made for milliseconds. A duration recorded in seconds puts every
value under ten seconds into the first three buckets and every percentile
comes out as `2.5`, `7.5` or `17.5`. Set boundaries for every histogram.

For durations between 5 ms and 10 minutes, in seconds:

```
DURATION_BOUNDARIES_SECONDS = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
    1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0,
)
```

Sixteen boundaries make seventeen buckets. Add a boundary at every threshold
you will alert on, because a backend that stores explicit buckets can place a
percentile no more precisely than the bucket that contains it. On Elastic the
percentile is reported at the bucket's midpoint. Source: `histogramSample` in
`elastic/apm-data` `input/otlp/metrics.go`: the first bucket is reported at
half its upper bound, the last at its lower bound, every other at its
midpoint. Prometheus style stores interpolate inside the bucket instead; the
boundary is still the precision.

Install them with a View. `opentelemetry-python` 1.2x:

```python
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View

View(
    instrument_name="sahara.controller.poll.duration",
    aggregation=ExplicitBucketHistogramAggregation(boundaries=DURATION_BOUNDARIES_SECONDS),
)
```

`View(instrument_type=None, instrument_name=None, meter_name=None, meter_version=None,
meter_schema_url=None, name=None, description=None, attribute_keys=None,
aggregation=None, exemplar_reservoir_factory=None, instrument_unit=None)`.
`instrument_name` accepts a wildcard, so one View can cover
`sahara.*.duration`. Since 1.30.0 `create_histogram(...,
explicit_bucket_boundaries_advisory=...)` sets the same thing at the
instrument, and a View still wins when both exist. Use the View: it lives in
the setup recipe next to the vocabulary, not at a call site.

## Temporality

Temporality is the `temporality=` argument of `configure_metrics(...)` in
`recipes/python_meter_setup.py`, one of `cumulative` or `delta`. Which one
this installation wants is the `metric temporality` line of the installation
block in `backends/README.md`; read it, do not guess.

- `cumulative`, the default of the SDK and of the recipe. Prometheus, Mimir
  and VictoriaMetrics want it: a cumulative series survives a lost scrape or
  a lost export, and `rate()` is defined over it.
- `delta`. Elastic APM Server needs it, stated in
  `backends/elastic/overview.md`. Elastic documents: "Ingestion of
  OpenTelemetry metrics with the type Histogram is only supported with delta
  temporality" and "Histograms with cumulative temporality are dropped
  before being ingested into Elasticsearch."

Passing `temporality="delta"` builds the same table the OTLP exporter builds
for `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta`: delta for
`Counter`, `ObservableCounter` and `Histogram`, cumulative for
`UpDownCounter`, `ObservableUpDownCounter` and `ObservableGauge`. Setting it
in code means the environment cannot silently turn it back.

UNVERIFIED: that a self managed 8.x APM Server drops a cumulative histogram
rather than storing its growing counts. `metrics.go` on `main` has no
temporality check. Either way delta is the setting that works on Elastic. If
a collector sits in between and the SDK cannot be changed, the
`cumulativetodelta` processor converts "monotonic sum, histogram, and
exponential histogram metrics from cumulative to delta".

## Exponential histograms

`ExponentialBucketHistogramAggregation(max_size=160, max_scale=20, record_min_max=True)`
exists in `opentelemetry.sdk.metrics.view`. Elastic 8.x APM Server drops the
metric type as unsupported. Never use it against 8.x. In 9.x Elastic
documents a cluster setting `xpack.otel_data.histogram_field_type` with value
`exponential_histogram` for the managed OTLP endpoint. UNVERIFIED: support on
a self managed 9.x APM Server.

## When a histogram is wrong

| You actually want | Use |
| --- | --- |
| a total or a rate | counter, unit `{thing}` |
| the latest value | gauge |
| a distribution of something that has a span | nothing, `metrics/derived-or-emitted.md` |
| each individual value, to look at one | a span attribute, or a span event |
| fewer than about ten values per export | a span attribute; the histogram would be noise |

## Other backends

Other backends: the verdicts do not change; the stored shape is in
backends/<backend>/mapping.md and the differences in backends/paradigms.md.

## Verdict

The *Metrics* table row:

```
| sahara.controller.poll.duration | histogram | s | sahara.entity.definition | no |
```

and, in the `## Volume` section of `vocabulary.md`:

```
histogram boundaries: sahara.controller.poll.duration = DURATION_BOUNDARIES_SECONDS
temporality: <cumulative | delta>, from the metric temporality line of backends/README.md, passed to configure_metrics
```

## Never

- Never put a unit in a name. `sahara.controller.poll.duration`, unit `s`.
- Never record milliseconds into a histogram whose unit says `s`.
- Never ship a histogram with the default boundaries.
- Never change boundaries without a vocabulary change. Documents before and
  after do not merge into one percentile.
- Never leave the temporality unstated. It is one line in `backends/README.md`
  and one argument to `configure_metrics`; on Elastic the default
  `cumulative` drops every histogram.

## Stop and ask

- Durations span more than five orders of magnitude and sixteen boundaries
  cannot cover them. A person chooses two histograms or coarser buckets.
- Someone wants a unit that UCUM does not have.
