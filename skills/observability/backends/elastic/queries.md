# KQL queries to paste

verified against: Kibana 8.17 KQL reference, Elasticsearch 8.17 mapping API
reference, field names from `mapping.md`. Aggregations that KQL
cannot express are in `queries-dsl.md`.

Rename before pasting: the label keys `labels.sahara_cycle_id`,
`labels.sahara_environment_id`, `labels.sahara_entity_definition`,
`labels.sahara_entity_instance_id`, and the values in angle brackets. Take the
index spelling from the vocabulary's *Backend spelling* column, never from
the attribute key.

KQL goes in the APM app search bar, the Trace explorer, or Discover on a
data view whose pattern is `traces-apm-*` for spans and transactions,
`logs-apm.error-*` for errors, `logs-*` for logs.

## KQL rules that matter here

- `field : value` on keyword fields. Quote values with spaces or colons.
- `field : *` means the field exists.
- `and`, `or`, `not`, parentheses. Ranges `>= <=` on numbers and dates.
- Escape `\ ( ) : < > " *` with a backslash inside a value.
- A label key is `labels.<key_with_underscores>`. Never a dot inside the key.

## All spans of one cycle

Data view `traces-apm-*`:

```
labels.sahara_cycle_id : "<cycle id>"
```

Only spans, not transactions:

```
labels.sahara_cycle_id : "<cycle id>" and processor.event : "span"
```

Only the test transactions of the cycle:

```
labels.sahara_cycle_id : "<cycle id>" and processor.event : "transaction"
```

## All operations on one entity instance

Data view `traces-apm-*`:

```
labels.sahara_entity_instance_id : "<instance id>" and processor.event : "span"
```

Add the cycle when instance ids repeat across cycles:

```
labels.sahara_entity_instance_id : "<instance id>" and labels.sahara_cycle_id : "<cycle id>"
```

## Find one span by span id

Data view `traces-apm-*`:

```
span.id : "<16 hex characters>"
```

A transaction's own id lives in `transaction.id`; the whole trace is
`trace.id : "<32 hex characters>"`. Both ids are lowercase hex.

## Documents where a label has an unexpected type

There is no mapping conflict inside `labels.*`; a number lands in
`numeric_labels.*` instead. So the check is: does the key exist on the side
it must not.

An id that someone sent as a number:

```
numeric_labels.sahara_cycle_id : *
```

A count that someone sent as a string:

```
labels.sahara_retry_count : *
```

Anything Elasticsearch had to ignore, from `ignore_above`, `ignore_malformed`
or the field limit:

```
_ignored : *
```

Check the mapped type of both spellings at once, in Dev Tools:

```
GET traces-apm-*/_mapping/field/labels.sahara_cycle_id,numeric_labels.sahara_cycle_id
```

Expected: `labels.sahara_cycle_id` of type `keyword`, and no
`numeric_labels.sahara_cycle_id` at all.

## Spans that can become a dependency

Link 3 of the Dependencies chain in `screens.md`:

```
processor.event : "span" and span.destination.service.resource : *
```

One definition only:

```
processor.event : "span" and span.destination.service.resource : "<definition name>"
```

## Error documents for a service

Data view `logs-apm.error-*`:

```
processor.event : "error" and service.name : "<service name>"
```

One error group, only occurrences that have a trace:

```
error.grouping_key : "<grouping key>" and trace.id : *
```

Errors of one cycle:

```
processor.event : "error" and labels.sahara_cycle_id : "<cycle id>"
```

## Log lines for a trace id

Data view `logs-*`:

```
trace.id : "<32 hex characters>"
```

That returns application log records, error documents, and the span events
that were not exceptions, which have `event.kind : "event"`. To keep only
the application lines:

```
trace.id : "<32 hex characters>" and not processor.event : "error" and not event.kind : "event"
```

Lines outside any span carry no `trace.id`. Find those by the correlation
keys the logging filter adds:

```
labels.sahara_cycle_id : "<cycle id>" and not trace.id : *
```

UNVERIFIED: that an OTLP log record's attributes land in `labels.*` is read
from the apm-data source, not from a guide page. Confirm on one document in
Discover before building a dashboard on it.

## Never

- Never write `labels.sahara.cycle.id`. That field does not exist.
- Never search the Traces page for a field only child transactions carry.
- Never paste a query from memory. Copy it from here and rename.

## Stop and ask

- A query needs a field that no row of `mapping.md` produces.
