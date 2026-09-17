# Checks

Three scripts that judge an export mechanically. Run the one that matches the
signal you changed, on a real export, and paste its output into your answer.
Standard library only, Python 3.11. Keep `check_common.py` next to them.

| Script | Reads | Rules |
| --- | --- | --- |
| `check_spans.py --spans FILE [--vocabulary vocabulary.md] [--max-name-cardinality 200] [--time-tolerance-ms 1] [--json]` | span export | input-not-empty, ids-well-formed, vocabulary-sane, roots-are-units, one-parent, orphans (WARN), name-cardinality, names-in-vocabulary, kind-matches-vocabulary, required-attributes, attribute-types, label-values, forbidden-values, exit-spans-have-destination, errors-are-recorded, errors-without-exception (WARN), exceptions-set-status (WARN), time-sane, children-inside-parents (WARN), links-resolve, dotted-keys-note (INFO) |
| `check_metrics.py --metrics FILE [--vocabulary vocabulary.md] [--max-series 1000] [--json]` | OTLP/JSON metrics export | input-not-empty, names-in-vocabulary, name-shape, instrument-type, unit-present, labels-allowed, series-count, id-like-values, label-types, derived-metrics (WARN) |
| `check_logs.py --logs FILE [--vocabulary vocabulary.md] [--spans FILE] [--max-messages 200] [--json]` | JSON Lines logs | input-not-empty, fields-present, level-values, message-templates, trace-correlation, trace-ids-in-spans (WARN), required-fields, forbidden-keys, secrets, field-types |

Every rule prints `PASS`, `FAIL`, `WARN`, `SKIP` or `INFO`, a count, up to
five offenders and a note. `--json` prints the same as one JSON object.

## Exit codes

`0` when no rule is `FAIL`. `1` when any rule is `FAIL`. `WARN` and `INFO`
never change the exit code; read them anyway. `2` is an argument error.

## How to produce each input

- **Spans.** Register `traces/recipes/python_file_exporter.py` as a span
  processor. It writes one JSON object per span, one per line. The checker
  also reads OTLP/JSON (`resourceSpans[]`, hex ids, integer enums, 64 bit
  numbers as strings) and the `ConsoleSpanExporter` output of
  opentelemetry-python (`context.trace_id` as `0x...`).
- **Metrics.** Use an exporter that writes OTLP/JSON: the OpenTelemetry
  Collector `file` exporter (`path:` required, `format: json` is the default,
  one JSON object per line), fed by `otlphttp` from the SDK. Verify the first
  line of the file starts with `{"resourceMetrics"`.
  `OTEL_METRICS_EXPORTER=console` redirected to a file is not OTLP/JSON; it is
  `MetricsData.to_json()` with `resource_metrics` and plain dict attributes.
  The checker reads that shape too, best effort, but the OTLP file is the
  reference.
- **Logs.** Point the ECS JSON handler from `logs/recipes/` at a file. One
  object per line with `@timestamp`, `log.level`, `message`, `trace.id` and
  `span.id`. Nested objects such as `{"log": {"level": "info"}}` are read as
  dotted keys.
- **Vocabulary.** The project's `vocabulary.md`, filled from
  `core/vocabulary-template.md`. Tables are read by their header names, so
  keep the template's headers. A Spans row whose Name contains `*` is a glob,
  for a root span rule that builds the name, for example `tests/*::test_*`.
  In Correlation keys, Where accepts `every span`,
  `every span except <name> <name>`, `every log` and
  `every log inside a span`. Forbidden entries ending in `.*` are prefixes.
  Without a vocabulary the vocabulary rules print `SKIP` and say so.

## Fixtures

`fixtures/` holds a passing and a failing export for each signal plus the
vocabulary they are checked against. `sh fixtures/run_fixtures.sh` runs all
of them and prints `HARNESS PASS` when the good ones exit 0 and the bad ones
exit 1. Run it once after copying the folder somewhere new.

## What you paste into your answer

Paste the full output of every checker you ran, then this sentence with the
blanks filled in:

`Checked <file> with <checker> against <vocabulary.md or "no vocabulary">: exit <0 or 1>, <n> FAIL, <n> WARN, <n> SKIP.`

If you could not run a checker, write which one and why, and do not say the
task is done.

## Backend note

Elastic APM stores span attributes that are not ECS fields under `labels.*`
with dots replaced by underscores. The `dotted-keys-note` rule lists the keys
this applies to. Record the stored spelling in the vocabulary's Backend
spelling column. Details: `backends/elastic/mapping.md`.
