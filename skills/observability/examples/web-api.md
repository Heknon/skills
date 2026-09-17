# Worked example: HTTP JSON API with a background job

Follow this when the system is a web service. Copy the section order and the
verdict formats. Change the names, not the shape.

## 1. The system, in ten lines

`orders-api` is a FastAPI process. It serves `GET /orders/{order_id}` and
`POST /orders`. Orders live in Postgres, database `orders`.
A Redis cache fronts `GET /orders/{order_id}`; a miss reads Postgres and fills
the cache. `POST /orders` asks the partner API `shipping-partner` for a rate
quote over HTTPS and retries up to three times on timeout or 5xx. The same
process runs a scheduler that starts `orders.reconcile` every minute: it reads
orders stuck in `shipping`, asks the partner for their status, updates
Postgres. Each request carries a tenant in a header. The service is deployed
to `staging` and `production`, one process per container, several containers.

## 2. Unit of work

Facts, from `core/unit-of-work.md`:

1. Many times per run: a request, yes; a reconcile run, yes, once a minute; a
   database query, yes; the process, no.
2. Stable name before it runs: a request, the route template; a reconcile
   run, the job type `orders.reconcile`; a query, no, only the table.
3. Inside one process: request, yes; job, yes.
4. Named when asked what failed: "the POST /orders request", "the reconcile
   job". Not "the SELECT".
5. Nesting: none. A job is not inside a request.
6. Two candidates that do not nest: request and job. Two units.

```
unit: request
root span name: HTTP method, one space, route template, e.g. "GET /orders/{order_id}"
instance key: http.request.id
outer roots: none

unit: job
root span name: the job type, "orders.reconcile"
instance key: orders.job.run_id
outer roots: none
```

Both units carry `orders.unit.type`, `request` or `job`.

## 3. Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | `orders-api` |
| service.version | string | resource | service.version | git tag, e.g. `2.14.0` |
| deployment.environment | string | resource | service.environment | `staging` or `production` |
| orders.tenant.id | string | every span, every log | labels.orders_tenant_id | tenant header value; `-` in the job |
| http.request.id | string | every span, every log | labels.http_request_id | request uuid; `-` in the job |
| orders.job.run_id | string | every span, every log | labels.orders_job_run_id | `<job type>-<start time RFC3339>`; `-` in a request |

Both units carry all three keys, and a key that does not apply to the unit is
`-`. Every span and every log then has the same key set, so a search on a key
never misses a document and the checker can require the key everywhere.
`host.name` and `process.pid` are resource attributes. No logical worker id:
one process is one container.

## 4. Signal choice

| Fact | Verdict | Reason |
| --- | --- | --- |
| A request was served | span | starts, ends, can fail |
| A reconcile run happened | span | starts, ends, can fail |
| Redis get, Redis set | span | a call to another system |
| A Postgres query ran | span | a call to another system |
| The partner was called | span | a call to another system |
| The cache missed | span event on `cache.get` | a fact about one moment inside the get |
| A partner attempt failed and was retried | span event on `partner.quote` | a moment inside the call |
| An order was created | log, inside the span | an audit fact that must survive sampling |
| Orders waiting for reconciliation | metric, gauge | a number to chart, no unit around it |
| Request latency, rate, failure rate | derived | root spans already carry them |
| Partner latency | derived | `partner.quote` spans carry it |
| Configuration loaded at startup | log, outside any span | happens before any span |
| A reconcile run was skipped, previous still active | log, outside any span | no job root was started |

## 5. Names

| Raw | Varying part removed | Name | Tier | Varying part goes to |
| --- | --- | --- | --- | --- |
| `GET /orders/8f2a` | the id | `GET /orders/{order_id}` | name | `url.path` attribute |
| `POST /orders` | nothing | `POST /orders` | name | none |
| `orders.reconcile 2026-09-17T10:04:00Z` | the start time | `orders.reconcile` | name | `orders.job.run_id` attribute |
| `SELECT * FROM orders WHERE id=$1` | the statement | `SELECT orders` | name | `db.statement` attribute |
| `GET order:8f2a` from Redis | the key | `cache.get` | name | `orders.cache.key` attribute |
| `https://api.shipping-partner.com/v2/quote` | the host, the path | `partner.quote` | name | `url.full` attribute |
| `orders_reconcile_backlog{tenant=acme}` | the tenant | `orders.reconcile.backlog` | metric name, no tenant label | none; tenant ids are unbounded |
| `order 8f2a created` | the id | `order created` | log template | `orders.order.id` field |

## 6. Parent or link decisions

- The job root has no parent and no link. The timer is not work.
- `SELECT orders` after a cache miss is a child of the request root, a sibling
  of `cache.get`. The get span has ended; the code ran in the handler.
- Retries are not spans. One `partner.quote` span per call, one
  `partner.retry` event per failed attempt, `orders.partner.attempts` on the
  span. The HTTP library's per-attempt spans, if enabled, are its children.
- `cache.set` after the read is a child of the request root. It ran there.
- No links at all: neither unit belongs to an outer thing.

## 7. Service, dependency, attribute decisions

- One service: `orders-api`. The scheduler is the same code in the same
  process, so it is not a second service.
- Dependencies, each a CLIENT span with a destination attribute:
  Postgres with `db.system=postgresql`, Redis with `db.system=redis`, the
  partner with `peer.service=shipping-partner`.
- Attributes: tenant id, request id, order id, cache key, partner attempt
  count. Labels: `orders.unit.type`, `orders.retry.reason`, `db.system`,
  `peer.service`.
- Route templates are names because FastAPI knows the template before the
  handler runs. `url.path` keeps the real path.

## 8. Errors

Status is set by the span wrapper: `OK` on clean exit, `ERROR` with the
exception recorded when the block raised. See `core/errors-and-status.md`.
An HTTP status code is a result, recorded in `http.response.status_code`; it
is not what decides the span status.

| Failure | Recorded as |
| --- | --- |
| Order not found, 404 | root status OK, `http.response.status_code=404`. Not an error. See `core/errors-and-status.md`. |
| Unhandled exception, 500 | root status ERROR, description is the exception message, `record_exception` on the span it was raised in |
| Partner attempt timed out, then succeeded | `partner.retry` event with `orders.retry.attempt`, `orders.retry.reason=timeout`; span status OK |
| Partner failed all three attempts | `partner.quote` status ERROR with `record_exception`; the handler returns 502, so the root is ERROR too |
| Redis unreachable | `cache.get` status ERROR with `record_exception`; the handler falls back to Postgres, so the root is OK |
| Postgres error in the job for one order | `SELECT orders` or `UPDATE orders` status ERROR with the exception; the job continues; `orders.job.failed_items` counts it; the root ends OK |
| Job root itself raises | root status ERROR, `record_exception` |

## 9. The vocabulary

```markdown
# Vocabulary: orders-api

backend: Elastic Stack 8, from backends/README.md
verified against: fill in from the running system on the day you check

## Unit of work

unit: request
root span name: HTTP method, one space, route template, e.g. "GET /orders/{order_id}"
instance key: http.request.id
outer roots: none

unit: job
root span name: the job type, "orders.reconcile"
instance key: orders.job.run_id
outer roots: none

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | orders-api |
| service.version | string | resource | service.version | git tag |
| deployment.environment | string | resource | service.environment | staging or production |
| orders.tenant.id | string | every span, every log | labels.orders_tenant_id | tenant header; - in the job |
| http.request.id | string | every span, every log | labels.http_request_id | request uuid; - in the job |
| orders.job.run_id | string | every span, every log | labels.orders_job_run_id | <job type>-<start RFC3339>; - in a request |

UNVERIFIED: http.request.id is also an ECS field name; whether the backend keeps it as
http.request.id or writes labels.http_request_id is in backends/elastic/mapping.md.

## Spans

| Name | Kind | Root | Required attributes | Destination attribute | Fails when |
| --- | --- | --- | --- | --- | --- |
| GET /orders/{order_id} | SERVER | yes | http.request.method, http.route, http.response.status_code, url.path, orders.unit.type | none | the handler raised |
| POST /orders | SERVER | yes | http.request.method, http.route, http.response.status_code, url.path, orders.unit.type | none | the handler raised, including a 502 after the partner failed |
| orders.reconcile | INTERNAL | yes | orders.unit.type, orders.job.items, orders.job.failed_items | none | the run itself raised; one failed item does not |
| cache.get | CLIENT | no | orders.cache.key | db.system | Redis unreachable; a miss is an event |
| cache.set | CLIENT | no | orders.cache.key | db.system | Redis unreachable |
| SELECT orders | CLIENT | no | db.statement, db.name | db.system | the driver raised |
| INSERT orders | CLIENT | no | db.statement, db.name | db.system | the driver raised |
| UPDATE orders | CLIENT | no | db.statement, db.name | db.system | the driver raised |
| partner.quote | CLIENT | no | http.request.method, url.full, orders.partner.attempts | peer.service | all attempts failed; then there is no http.response.status_code |
| partner.status | CLIENT | no | http.request.method, url.full, orders.partner.attempts | peer.service | all attempts failed; then there is no http.response.status_code |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| orders.unit.type | string | label | request, job | labels.orders_unit_type |
| orders.retry.reason | string | label | timeout, status_5xx, connection_error | event attribute |
| db.system | string | label | postgresql, redis | per backends/elastic/mapping.md |
| peer.service | string | label | shipping-partner | per backends/elastic/mapping.md |
| orders.job.items | int | attribute | unbounded | labels.orders_job_items |
| orders.job.failed_items | int | attribute | unbounded | labels.orders_job_failed_items |
| orders.order.id | string | attribute | unbounded | labels.orders_order_id |
| orders.cache.key | string | attribute | unbounded | labels.orders_cache_key |
| orders.partner.attempts | int | attribute | unbounded | labels.orders_partner_attempts |
| orders.retry.attempt | int | attribute | unbounded | event attribute |
| http.request.method | string | attribute | unbounded | per backends/elastic/mapping.md |
| http.route | string | attribute | unbounded | per backends/elastic/mapping.md |
| http.response.status_code | int | attribute | unbounded | per backends/elastic/mapping.md |
| url.path | string | attribute | unbounded | per backends/elastic/mapping.md |
| url.full | string | attribute | unbounded | per backends/elastic/mapping.md |
| db.name | string | attribute | unbounded | per backends/elastic/mapping.md |
| db.statement | string | attribute | unbounded | per backends/elastic/mapping.md |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| exception | any | exception.type, exception.message, exception.stacktrace, exception.escaped |
| cache.miss | cache.get | orders.cache.key |
| partner.retry | partner.quote, partner.status | orders.retry.attempt, orders.retry.reason |

## Links

| From span | To span | link.relation |
| --- | --- | --- |

No links: neither unit belongs to an outer thing, and a retry is an event,
not a span.

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| orders.reconcile.backlog | gauge | {order} | (none) | no |
| orders.request.duration | none | s | (none) | yes, derived: see backends/elastic/screens.md |
| orders.partner.duration | none | s | (none) | yes, derived: see backends/elastic/screens.md |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| configuration loaded | info | orders.config.path | yes |
| reconcile run skipped, previous run still active | warn | orders.job.run_id, orders.tenant.id | yes |
| order created | info | orders.order.id, orders.tenant.id, http.request.id, trace.id, span.id | no |

## Boundaries

Inbound: the FastAPI instrumentation reads traceparent from the caller, so a
request continues the caller's trace when there is one; the tenant header
becomes orders.tenant.id. Outbound: the HTTP client instrumentation injects
traceparent into partner calls, so the partner's spans, if it emits any, join
the trace. The scheduler starts each job with a fresh context; a job never
continues a request's trace.

## Long lived things

The process and the scheduler outlive every unit; neither has a span. An
order stuck in shipping is a state in Postgres, counted by
orders.reconcile.backlog, not a span left open.

## Lanes and time

Several containers, one process and one SDK each; host.name tells them
apart. Every container reads the same table, so orders.reconcile.backlog is
read with max across containers, not sum.

## Volume

Requests are head sampled when volume needs it; order created is a log so the
audit fact survives sampling. Jobs are never sampled.

## Forbidden

- `http.request.header.*`, `http.response.header.*`, `orders.partner.payload*`
- order ids, request ids, tenant ids, cache keys, full URLs, SQL literals and partner payloads never appear in a span name, metric name, metric label or log template

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | example author | first version |
```

## 10. Golden trace

Every line is what `traces/recipes/python_file_exporter.py` writes for one
span. Status is `OK` on clean exit, `ERROR` where an exception was recorded.

```jsonl
// Request unit. Root SERVER span, route template as the name, 200 after a cache miss. The job key is "-" on a request.
{"name":"GET /orders/{order_id}","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7","parent_span_id":null,"kind":"SERVER","start_time_unix_nano":1789639200000000000,"end_time_unix_nano":1789639200412000000,"status":{"code":"OK","description":null},"attributes":{"http.request.method":"GET","http.route":"/orders/{order_id}","url.path":"/orders/8f2a","http.response.status_code":200,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production","host.name":"orders-7c9d","process.pid":41},"events":[],"links":[]}
// Cache read. CLIENT with db.system so it is a dependency. The miss is an event, not a log.
{"name":"cache.get","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"1a2b3c4d5e6f7081","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200001000000,"end_time_unix_nano":1789639200003000000,"status":{"code":"OK","description":null},"attributes":{"db.system":"redis","orders.cache.key":"order:8f2a","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"cache.miss","time_unix_nano":1789639200002500000,"attributes":{"orders.cache.key":"order:8f2a"}}],"links":[]}
// Database read after the miss. Sibling of cache.get, child of the root. Name is verb plus table.
{"name":"SELECT orders","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"2b3c4d5e6f708192","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200004000000,"end_time_unix_nano":1789639200021000000,"status":{"code":"OK","description":null},"attributes":{"db.system":"postgresql","db.name":"orders","db.statement":"SELECT id, tenant_id, state, total FROM orders WHERE id = $1","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// Partner call. One span for the whole call; the first attempt timed out and is an event; the second succeeded, so the span is OK.
{"name":"partner.quote","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"3c4d5e6f708192a3","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200022000000,"end_time_unix_nano":1789639200405000000,"status":{"code":"OK","description":null},"attributes":{"peer.service":"shipping-partner","http.request.method":"POST","url.full":"https://api.shipping-partner.com/v2/quote","http.response.status_code":200,"orders.partner.attempts":2,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"partner.retry","time_unix_nano":1789639200222000000,"attributes":{"orders.retry.attempt":1,"orders.retry.reason":"timeout"}}],"links":[]}
// Cache fill. Same key attribute as the get, so one search finds both.
{"name":"cache.set","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"4d5e6f708192a3b4","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200406000000,"end_time_unix_nano":1789639200408000000,"status":{"code":"OK","description":null},"attributes":{"db.system":"redis","orders.cache.key":"order:8f2a","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// A second request, different trace. 404 is a result, not an error: the handler returned, so the status is OK and the code is the attribute.
{"name":"GET /orders/{order_id}","trace_id":"7d3f0c9a2b1e4f5a8c6d7e8f90a1b2c3","span_id":"5e6f708192a3b4c5","parent_span_id":null,"kind":"SERVER","start_time_unix_nano":1789639201000000000,"end_time_unix_nano":1789639201019000000,"status":{"code":"OK","description":null},"attributes":{"http.request.method":"GET","http.route":"/orders/{order_id}","url.path":"/orders/does-not-exist","http.response.status_code":404,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"0b7d6a4c-1e2f-4a3b-9c8d-7e6f5a4b3c2d","orders.job.run_id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// Job unit. Own trace, no parent, no link. Name is the job type; the start time is an attribute. The request keys are "-" on a job.
{"name":"orders.reconcile","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"6f708192a3b4c5d6","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789639440000000000,"end_time_unix_nano":1789639442310000000,"status":{"code":"OK","description":null},"attributes":{"orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-","http.request.id":"-","orders.job.items":12,"orders.job.failed_items":1},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// The job's read.
{"name":"SELECT orders","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"708192a3b4c5d6e7","parent_span_id":"6f708192a3b4c5d6","kind":"CLIENT","start_time_unix_nano":1789639440001000000,"end_time_unix_nano":1789639440030000000,"status":{"code":"OK","description":null},"attributes":{"db.system":"postgresql","db.name":"orders","db.statement":"SELECT id, tenant_id FROM orders WHERE state = $1","orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-","http.request.id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// A partner status call that failed all three attempts. ERROR on this span with the exception; the job root above ended OK and counted the item.
{"name":"partner.status","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"8192a3b4c5d6e7f8","parent_span_id":"6f708192a3b4c5d6","kind":"CLIENT","start_time_unix_nano":1789639440031000000,"end_time_unix_nano":1789639441650000000,"status":{"code":"ERROR","description":"ReadTimeout: partner did not answer in 500 ms after 3 attempts"},"attributes":{"peer.service":"shipping-partner","http.request.method":"GET","url.full":"https://api.shipping-partner.com/v2/shipments/8f2a","orders.partner.attempts":3,"orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-","http.request.id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"partner.retry","time_unix_nano":1789639440540000000,"attributes":{"orders.retry.attempt":1,"orders.retry.reason":"timeout"}},{"name":"partner.retry","time_unix_nano":1789639441090000000,"attributes":{"orders.retry.attempt":2,"orders.retry.reason":"timeout"}},{"name":"exception","time_unix_nano":1789639441650000000,"attributes":{"exception.type":"httpx.ReadTimeout","exception.message":"partner did not answer in 500 ms after 3 attempts","exception.stacktrace":"Traceback (most recent call last): ...","exception.escaped":"True"}}],"links":[]}
```

The golden metric is one OTLP/JSON document, what the collector `file`
exporter writes. A gauge with no tenant label and no run id: only the
resource identifies the series.

```json
{
  "resourceMetrics": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "orders-api"}},
          {"key": "service.version", "value": {"stringValue": "2.14.0"}},
          {"key": "deployment.environment", "value": {"stringValue": "production"}},
          {"key": "host.name", "value": {"stringValue": "orders-7c9d"}}
        ]
      },
      "scopeMetrics": [
        {
          "scope": {"name": "orders_api", "version": "2.14.0"},
          "metrics": [
            {
              "name": "orders.reconcile.backlog",
              "unit": "{order}",
              "gauge": {
                "dataPoints": [
                  {"attributes": [], "timeUnixNano": "1789639442000000000", "asInt": "12"}
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

The golden logs are ECS lines, what the handler in `logs/recipes/` writes:
`@timestamp`, `log.level` in upper case, `message`, the correlation keys by
their OpenTelemetry names, and `trace.id` plus `span.id` when the line was
written inside a span. The index-side names after the shipper's renames are
in `backends/elastic/mapping.md`.

```jsonl
// Inside a span: the audit fact from POST /orders. The handler added the keys and the trace ids.
{"@timestamp":"2026-09-17T10:00:07.412Z","log.level":"INFO","message":"order created","ecs.version":"8.11.0","log.logger":"orders_api.orders","orders.order.id":"8f2a","orders.tenant.id":"acme","http.request.id":"c3d4e5f6-0a1b-4c2d-8e3f-4a5b6c7d8e9f","orders.job.run_id":"-","orders.unit.type":"request","trace.id":"c0ffee0000000000000000000000abcd","span.id":"a3b4c5d6e7f80910"}
// Outside any span: no job root was started, so there is no trace.id and no span.id. The keys come from the logging filter, from the vocabulary module.
{"@timestamp":"2026-09-17T10:05:00.000Z","log.level":"WARN","message":"reconcile run skipped, previous run still active","ecs.version":"8.11.0","log.logger":"orders_api.scheduler","orders.job.run_id":"orders.reconcile-2026-09-17T10:05:00Z","orders.tenant.id":"-","http.request.id":"-","orders.unit.type":"job"}
```

## 11. What Kibana shows

This example's backend is Elastic. On another backend the verdicts above do
not change; the screens are in `backends/<backend>/screens.md` and the
differences in `backends/paradigms.md`. Screen names here are from
`backends/elastic/screens.md`; it has the path and the grouping field of
each.

1. Services lists one service, `orders-api`, per `service.environment`.
2. Transactions lists `GET /orders/{order_id}`, `POST /orders` and
   `orders.reconcile`; filter on `labels.orders_unit_type` to separate them.
3. Dependencies lists `shipping-partner` from `peer.service`; Postgres and
   Redis appear the way that file says `db.system` exit spans appear.
4. The trace waterfall for one request shows `cache.get` with its `cache.miss`
   event, then `SELECT orders`, `partner.quote` with its retry event, `cache.set`.
5. Errors groups the `ReadTimeout` from `partner.status`; the 404 request never
   appears there. Discover finds the two log lines by `labels.orders_job_run_id`
   or by `trace.id`.
