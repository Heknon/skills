# Elasticsearch DSL to paste

verified against: Elasticsearch 8.17 references for the `terms`,
`percentiles`, `date_histogram`, `filter` and `cardinality` aggregations and
the `_ignored` field. Field names from `mapping.md`.

Rename before pasting: the label keys and every value in angle brackets, as
in `queries.md`. Paste each body in **Dev Tools > Console** after the `GET`
line shown. `<namespace>` is `default` unless the integration policy says
otherwise.

## Latency percentiles of one span name grouped by a label

`GET traces-apm-*/_search`. `span.duration.us` is a `long` in microseconds.
Percentiles are approximate, TDigest.

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

`GET traces-apm-*/_search`. Rate = `failed.doc_count / doc_count` per
bucket. Documents with `event.outcome: unknown` count in the total and not
in `failed`, which is why status must never be left `UNSET`.

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
`GET metrics-apm.transaction.60m-<namespace>/_search` filtered on
`metricset.name: transaction`, with a `sum` on `_doc_count` per
`event.outcome`. Never `value_count` there: one document is many events.

## Count of distinct values of a label

`GET traces-apm-*/_search`. Approximate above `precision_threshold`,
default 3000, maximum 40000. Run it before a key is promoted to the label
tier, and again when a chart grows singletons.

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

## Which fields Elasticsearch ignored, and how often

`GET traces-apm-*/_search`.

```json
{
  "size": 0,
  "query": { "exists": { "field": "_ignored" } },
  "aggs": { "ignored_fields": { "terms": { "field": "_ignored", "size": 50 } } }
}
```

## Which transactions have a given dependency

A span document carries `transaction.id` and `trace.id`, not
`transaction.name`. Two steps.

Step 1, `GET traces-apm-*/_search`: the transaction ids of spans with the
resource.

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

Step 2, KQL in Discover with the ids from step 1:

```
processor.event : "transaction" and transaction.id : ("<id 1>" or "<id 2>")
```

Which services call the resource, without the two steps:
`GET metrics-apm.service_destination.1m-<namespace>/_search`.

```json
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "span.destination.service.resource": "<definition name>" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "callers": {
      "terms": { "field": "service.name", "size": 50 },
      "aggs": {
        "calls": { "sum": { "field": "span.destination.service.response_time.count" } },
        "total_us": { "sum": { "field": "span.destination.service.response_time.sum.us" } }
      }
    }
  }
}
```

Average latency per caller is `total_us / calls`. That is the number the
Dependencies screen shows.

## Errors of one cycle by exception type

`GET logs-apm.error-*/_search`.

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

## Never

- Never aggregate on a `text` field. Every field named here is keyword or
  numeric.
- Never use `value_count` on an aggregated metrics stream. Sum `_doc_count`
  or the `.count` field.
- Never run a `terms` aggregation on `numeric_labels.*` to list ids. If an id
  is there, the type is wrong; see `queries.md`.

## Stop and ask

- The cardinality check returns more than a few hundred for a key the
  vocabulary calls a label.
- An aggregation needs a field that no row of `mapping.md`
  produces.
