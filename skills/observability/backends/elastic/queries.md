# Queries to paste

verified against: Kibana 8.17 KQL reference, Elasticsearch 8.17 aggregation
and mapping API references, field names from `apm-server-mapping.md`.

Rename before pasting: the label keys `labels.sahara_cycle_id`,
`labels.sahara_environment_id`, `labels.sahara_entity_definition`,
`labels.sahara_entity_instance_id`, and the values in angle brackets. Take the
index spelling from the vocabulary's *Backend spelling* column, never from
the attribute key. `<namespace>` is `default` unless the integration policy
says otherwise.

KQL goes in the APM app search bar, the Trace explorer, or Discover on a
data view whose pattern is `traces-apm-*` for spans and transactions,
`logs-apm.error-*` for errors, `logs-*` for logs. DSL goes in
**Dev Tools > Console** as `GET <pattern>/_search` with the body shown.

## KQL rules that matter here

- `field : value` on keyword fields. Quote values with spaces or colons.
- `field : *` means the field exists.
- `and`, `or`, `not`, parentheses. Ranges `>= <=` on numbers and dates.
- Escape `\ ( ) : < > " *` with a backslash inside a value.
- A label key is `labels.<key_with_underscores>`. Never a dot inside the key.

## All spans of one cycle

KQL, data view `traces-apm-*`:

```
labels.sahara_cycle_id : "<cycle id>"
```

Only spans, not transactions:

```
labels.sahara_cycle_id : "<cycle id>" and processor.event : "span"
```

Only the test transactions of the cycle, newest first in Discover:

```
labels.sahara_cycle_id : "<cycle id>" and processor.event : "transaction"
```

## All operations on one entity instance

KQL, data view `traces-apm-*`:

```
labels.sahara_entity_instance_id : "<instance id>" and processor.event : "span"
```

Add the cycle when instance ids repeat across cycles:

```
labels.sahara_entity_instance_id : "<instance id>" and labels.sahara_cycle_id : "<cycle id>"
```

## Latency percentiles of one span name grouped by a label

DSL, `GET traces-apm-*/_search`. `span.duration.us` is a `long` in
microseconds. Percentiles are approximate, TDigest.

```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "processor.event": "span" } },
        { "term": { "span.name": "entity.create" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "by_definition": {
      "terms": { "field": "labels.sahara_entity_definition", "size": 50 },
      "aggs": {
        "latency": {
          "percentiles": { "field": "span.duration.us", "percents": [50, 95, 99] }
        }
      }
    }
  }
}
```

## Failed transaction rate per transaction name over time

DSL, `GET traces-apm-*/_search`. Rate = `failed.doc_count / total doc_count`
per bucket. Documents with `event.outcome: unknown` count in the total and
not in `failed`, which is why status must never be left `UNSET`.

```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "processor.event": "transaction" } },
        { "term": { "service.name": "<service name>" } },
        { "range": { "@timestamp": { "gte": "now-7d" } } }
      ]
    }
  },
  "aggs": {
    "by_name": {
      "terms": { "field": "transaction.name", "size": 200 },
      "aggs": {
        "over_time": {
          "date_histogram": { "field": "@timestamp", "fixed_interval": "1h" },
          "aggs": {
            "failed": { "filter": { "term": { "event.outcome": "failure" } } }
          }
        }
      }
    }
  }
}
```

The same over the pre-aggregated stream, cheaper for long ranges:
`GET metrics-apm.transaction.60m-<namespace>/_search` with the filter
`metricset.name: transaction`, summing `_doc_count` per bucket and per
`event.outcome`. Use `sum` on `_doc_count`, not `value_count`.

## Find one span by span id

KQL, data view `traces-apm-*`:

```
span.id : "<16 hex characters>"
```

A transaction's own id lives in `transaction.id`; the whole trace is
`trace.id : "<32 hex characters>"`. Both ids are lowercase hex.

## Documents where a label has an unexpected type

There is no mapping conflict inside `labels.*`; a number lands in
`numeric_labels.*` instead. So the check is: does the key exist on the side
it must not.

KQL, an id that someone sent as a number:

```
numeric_labels.sahara_cycle_id : *
```

KQL, a count that someone sent as a string:

```
labels.sahara_retry_count : *
```

KQL, anything Elasticsearch had to ignore, from `ignore_above`,
`ignore_malformed` or the field limit:

```
_ignored : *
```

DSL, which fields were ignored and how often:

```json
{
  "size": 0,
  "query": { "exists": { "field": "_ignored" } },
  "aggs": { "ignored_fields": { "terms": { "field": "_ignored", "size": 50 } } }
}
```

Check the mapped type of both spellings at once:

```
GET traces-apm-*/_mapping/field/labels.sahara_cycle_id,numeric_labels.sahara_cycle_id
```

Expected: `labels.sahara_cycle_id` of type `keyword`, and no
`numeric_labels.sahara_cycle_id` at all.

## Count of distinct values of a label

DSL, `GET traces-apm-*/_search`. Approximate above
`precision_threshold`, default 3000, maximum 40000. Run it before a key is
promoted to the label tier, and again when a chart grows singletons.

```json
{
  "size": 0,
  "query": { "range": { "@timestamp": { "gte": "now-30d" } } },
  "aggs": {
    "distinct_definitions": {
      "cardinality": { "field": "labels.sahara_entity_definition", "precision_threshold": 40000 }
    }
  }
}
```

## Which transactions have a given dependency

A span document carries `transaction.id` and `trace.id`, not
`transaction.name`. Two steps.

Step 1, DSL on `GET traces-apm-*/_search`: the transaction ids of spans with
the resource.

```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "processor.event": "span" } },
        { "term": { "span.destination.service.resource": "<definition name>" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "transactions": { "terms": { "field": "transaction.id", "size": 500 } }
  }
}
```

Step 2, KQL with the ids from step 1:

```
processor.event : "transaction" and transaction.id : ("<id 1>" or "<id 2>")
```

Spans with any destination, the check for link 3 of the Dependencies chain:

```
processor.event : "span" and span.destination.service.resource : *
```

Which services call the resource, without the two steps:
`GET metrics-apm.service_destination.1m-<namespace>/_search` with a `terms`
aggregation on `service.name` under the filter
`span.destination.service.resource: <definition name>`.

## Error documents for a service

KQL, data view `logs-apm.error-*`:

```
processor.event : "error" and service.name : "<service name>"
```

One error group, then its traces:

```
error.grouping_key : "<grouping key>" and trace.id : *
```

Errors of one cycle, by exception type, DSL on
`GET logs-apm.error-*/_search`:

```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "labels.sahara_cycle_id": "<cycle id>" } }
      ]
    }
  },
  "aggs": {
    "by_type": { "terms": { "field": "error.exception.type", "size": 50 } }
  }
}
```

## Log lines for a trace id

KQL, data view `logs-*`:

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

UNVERIFIED: the field a log record's attributes land in is `labels.*` on
this path per the apm-data source; confirm on one document with Discover
before building a dashboard on it.

## Never

- Never aggregate on a `text` field. Every field named here is keyword or
  numeric.
- Never write `labels.sahara.cycle.id`. That field does not exist.
- Never use `value_count` on an aggregated metrics stream. Sum `_doc_count`.

## Stop and ask

- A query needs a field that no row of `apm-server-mapping.md` produces.
- The cardinality check returns more than a few hundred for a key the
  vocabulary calls a label.
