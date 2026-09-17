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
| orders.tenant.id | string | every span, every log | labels.orders_tenant_id | tenant header value; `-` for the job |
| http.request.id | string | every span, every log | labels.http_request_id | request uuid, request unit only |
| orders.job.run_id | string | every span, every log | labels.orders_job_run_id | `<job type>-<start time RFC3339>`, job unit only |

`host.name` and `process.pid` are resource attributes. No logical worker id: one
process is one container.

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
- The partner's retries are not spans. One `partner.quote` span per call, one
  `partner.retry` event per failed attempt, `orders.partner.attempts` on the
  span. The HTTP client library's own per-attempt spans, if its
  instrumentation is enabled, are children of `partner.quote`.
- `cache.set` after the read is a child of the request root. It ran there.

## 7. Service, dependency, attribute decisions

- One service: `orders-api`. The scheduler is the same code in the same
  process, so it is not a second service.
- Dependencies, each a CLIENT span with a destination attribute:
  Postgres with `db.system=postgresql`, Redis with `db.system=redis`, the
  partner with `peer.service=shipping-partner`.
- Attributes: tenant id, request id, order id, cache key, partner attempt
  count. Labels: `orders.unit.type`, `orders.retry.reason`.
- Route templates are names because FastAPI knows the template before the
  handler runs. `url.path` keeps the real path.

## 8. Errors

| Failure | Recorded as |
| --- | --- |
| Order not found, 404 | root status UNSET, `http.response.status_code=404`. Not an error. See `core/errors-and-status.md`. |
| Unhandled exception, 500 | root status ERROR, description is the exception message, `record_exception` on the span it was raised in |
| Partner attempt timed out, then succeeded | `partner.retry` event with `orders.retry.attempt`, `orders.retry.reason=timeout`; span status UNSET |
| Partner failed all three attempts | `partner.quote` status ERROR with `record_exception`; the handler returns 502, so the root is ERROR too |
| Redis unreachable | `cache.get` status ERROR with `record_exception`; the handler falls back to Postgres, so the root is not an error |
| Postgres error in the job for one order | `SELECT orders` or `UPDATE orders` status ERROR with the exception; the job continues; `orders.job.failed_items` counts it; the root stays UNSET |
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
| orders.tenant.id | string | every span, every log | labels.orders_tenant_id | tenant header; "-" for the job |
| http.request.id | string | every span, every log | labels.http_request_id | request uuid, request unit only |
| orders.job.run_id | string | every span, every log | labels.orders_job_run_id | <job type>-<start RFC3339>, job unit only |

UNVERIFIED: http.request.id is also an ECS field name; whether APM Server keeps it as
http.request.id or writes labels.http_request_id is in backends/elastic/apm-server-mapping.md.

## Spans

| Name | Kind | Root | Required attributes | Destination attribute (CLIENT and PRODUCER only) |
| --- | --- | --- | --- | --- |
| GET /orders/{order_id} | SERVER | yes | http.request.method, http.route, http.response.status_code, url.path, orders.unit.type | none |
| POST /orders | SERVER | yes | http.request.method, http.route, http.response.status_code, url.path, orders.unit.type | none |
| orders.reconcile | INTERNAL | yes | orders.unit.type, orders.job.items, orders.job.failed_items | none |
| cache.get | CLIENT | no | orders.cache.key | db.system=redis |
| cache.set | CLIENT | no | orders.cache.key | db.system=redis |
| SELECT orders | CLIENT | no | db.statement, db.name | db.system=postgresql |
| INSERT orders | CLIENT | no | db.statement, db.name | db.system=postgresql |
| UPDATE orders | CLIENT | no | db.statement, db.name | db.system=postgresql |
| partner.quote | CLIENT | no | http.request.method, url.full, http.response.status_code, orders.partner.attempts | peer.service=shipping-partner |
| partner.status | CLIENT | no | http.request.method, url.full, http.response.status_code, orders.partner.attempts | peer.service=shipping-partner |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| orders.unit.type | string | label | request, job | labels.orders_unit_type |
| orders.tenant.id | string | attribute | unbounded | labels.orders_tenant_id |
| http.request.id | string | attribute | unbounded | labels.http_request_id |
| orders.job.run_id | string | attribute | unbounded | labels.orders_job_run_id |
| orders.job.items | int | attribute | unbounded | labels.orders_job_items |
| orders.job.failed_items | int | attribute | unbounded | labels.orders_job_failed_items |
| orders.order.id | string | attribute | unbounded | labels.orders_order_id |
| orders.cache.key | string | attribute | unbounded | labels.orders_cache_key |
| orders.partner.attempts | int | attribute | unbounded | labels.orders_partner_attempts |
| orders.retry.attempt | int | attribute | unbounded | event attribute |
| orders.retry.reason | string | label | timeout, status_5xx, connection_error | event attribute |
| http.request.method, http.route, http.response.status_code, url.path, url.full, db.system, db.name, db.statement, peer.service | as emitted | attribute | per semantic conventions | per backends/elastic/apm-server-mapping.md |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| cache.miss | cache.get | orders.cache.key |
| partner.retry | partner.quote, partner.status | orders.retry.attempt, orders.retry.reason |

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| orders.reconcile.backlog | gauge | {order} | none | no |
| request latency, throughput, failure rate | none | none | none | yes, Transactions screen in backends/elastic/kibana-screens.md |
| partner latency and failure rate | none | none | none | yes, Dependencies screen in backends/elastic/kibana-screens.md |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| configuration loaded | info | orders.config.path | yes |
| reconcile run skipped, previous run still active | warning | orders.job.run_id, orders.tenant.id | yes |
| order created | info | orders.order.id, orders.tenant.id, http.request.id, trace.id, span.id | no |

## Forbidden

order ids, request ids, tenant ids, cache keys, URLs, SQL literals, partner
payloads, in any span name, metric name, metric label or log template.

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | example author | first version |
```

## 10. Golden trace

```jsonl
// Request unit. Root SERVER span, route template as the name, 200 after a cache miss.
{"name":"GET /orders/{order_id}","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"00f067aa0ba902b7","parent_span_id":null,"kind":"SERVER","start_time_unix_nano":1789639200000000000,"end_time_unix_nano":1789639200412000000,"status":{"code":"UNSET","description":null},"attributes":{"http.request.method":"GET","http.route":"/orders/{order_id}","url.path":"/orders/8f2a","http.response.status_code":200,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production","host.name":"orders-7c9d","process.pid":41},"events":[],"links":[]}
// Cache read. CLIENT with db.system so it is a dependency. The miss is an event, not a log.
{"name":"cache.get","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"1a2b3c4d5e6f7081","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200001000000,"end_time_unix_nano":1789639200003000000,"status":{"code":"UNSET","description":null},"attributes":{"db.system":"redis","orders.cache.key":"order:8f2a","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"cache.miss","time_unix_nano":1789639200002500000,"attributes":{"orders.cache.key":"order:8f2a"}}],"links":[]}
// Database read after the miss. Sibling of cache.get, child of the root. Name is verb plus table.
{"name":"SELECT orders","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"2b3c4d5e6f708192","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200004000000,"end_time_unix_nano":1789639200021000000,"status":{"code":"UNSET","description":null},"attributes":{"db.system":"postgresql","db.name":"orders","db.statement":"SELECT id, tenant_id, state, total FROM orders WHERE id = $1","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// Partner call. One span for the whole call; the first attempt timed out and is an event; the second succeeded.
{"name":"partner.quote","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"3c4d5e6f708192a3","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200022000000,"end_time_unix_nano":1789639200405000000,"status":{"code":"UNSET","description":null},"attributes":{"peer.service":"shipping-partner","http.request.method":"POST","url.full":"https://api.shipping-partner.com/v2/quote","http.response.status_code":200,"orders.partner.attempts":2,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"partner.retry","time_unix_nano":1789639200222000000,"attributes":{"orders.retry.attempt":1,"orders.retry.reason":"timeout"}}],"links":[]}
// Cache fill. Same key attribute as the get, so one search finds both.
{"name":"cache.set","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"4d5e6f708192a3b4","parent_span_id":"00f067aa0ba902b7","kind":"CLIENT","start_time_unix_nano":1789639200406000000,"end_time_unix_nano":1789639200408000000,"status":{"code":"UNSET","description":null},"attributes":{"db.system":"redis","orders.cache.key":"order:8f2a","orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"9e1c2b4a-5f60-4d7e-8a9b-0c1d2e3f4a5b"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// A second request, different trace. 404 is a result, not an error: status stays UNSET.
{"name":"GET /orders/{order_id}","trace_id":"7d3f0c9a2b1e4f5a8c6d7e8f90a1b2c3","span_id":"5e6f708192a3b4c5","parent_span_id":null,"kind":"SERVER","start_time_unix_nano":1789639201000000000,"end_time_unix_nano":1789639201019000000,"status":{"code":"UNSET","description":null},"attributes":{"http.request.method":"GET","http.route":"/orders/{order_id}","url.path":"/orders/does-not-exist","http.response.status_code":404,"orders.unit.type":"request","orders.tenant.id":"acme","http.request.id":"0b7d6a4c-1e2f-4a3b-9c8d-7e6f5a4b3c2d"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// Job unit. Own trace, no parent, no link. Name is the job type; the start time is an attribute.
{"name":"orders.reconcile","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"6f708192a3b4c5d6","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789639440000000000,"end_time_unix_nano":1789639442310000000,"status":{"code":"UNSET","description":null},"attributes":{"orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-","orders.job.items":12,"orders.job.failed_items":1},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// The job's read.
{"name":"SELECT orders","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"708192a3b4c5d6e7","parent_span_id":"6f708192a3b4c5d6","kind":"CLIENT","start_time_unix_nano":1789639440001000000,"end_time_unix_nano":1789639440030000000,"status":{"code":"UNSET","description":null},"attributes":{"db.system":"postgresql","db.name":"orders","db.statement":"SELECT id, tenant_id FROM orders WHERE state = $1","orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[],"links":[]}
// A partner status call that failed all three attempts. ERROR on this span; the job root above is not an error.
{"name":"partner.status","trace_id":"9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d","span_id":"8192a3b4c5d6e7f8","parent_span_id":"6f708192a3b4c5d6","kind":"CLIENT","start_time_unix_nano":1789639440031000000,"end_time_unix_nano":1789639441650000000,"status":{"code":"ERROR","description":"ReadTimeout: partner did not answer in 500 ms after 3 attempts"},"attributes":{"peer.service":"shipping-partner","http.request.method":"GET","url.full":"https://api.shipping-partner.com/v2/shipments/8f2a","orders.partner.attempts":3,"orders.unit.type":"job","orders.job.run_id":"orders.reconcile-2026-09-17T10:04:00Z","orders.tenant.id":"-"},"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"},"events":[{"name":"partner.retry","time_unix_nano":1789639440540000000,"attributes":{"orders.retry.attempt":1,"orders.retry.reason":"timeout"}},{"name":"partner.retry","time_unix_nano":1789639441090000000,"attributes":{"orders.retry.attempt":2,"orders.retry.reason":"timeout"}},{"name":"exception","time_unix_nano":1789639441650000000,"attributes":{"exception.type":"httpx.ReadTimeout","exception.message":"partner did not answer in 500 ms after 3 attempts","exception.stacktrace":"Traceback (most recent call last): ..."}}],"links":[]}
```

```jsonl
// Metric data point. A gauge, no tenant label, no run id: only resource attributes identify it.
{"name":"orders.reconcile.backlog","unit":"{order}","instrument":"gauge","data_points":[{"attributes":{},"time_unix_nano":1789639442000000000,"value":12}],"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"}}
```

```jsonl
// Log line inside a span: the audit fact from POST /orders. trace_id and span_id injected by the logging setup; the index-side names are in backends/elastic/apm-server-mapping.md.
{"body":"order created","severity_text":"INFO","attributes":{"orders.order.id":"8f2a","orders.tenant.id":"acme","http.request.id":"c3d4e5f6-0a1b-4c2d-8e3f-4a5b6c7d8e9f","orders.unit.type":"request"},"trace_id":"c0ffee0000000000000000000000abcd","span_id":"a3b4c5d6e7f80910","resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"}}
// Log line outside any span: no trace ids exist, so the correlation keys are set by the logging filter from the vocabulary module.
{"body":"reconcile run skipped, previous run still active","severity_text":"WARNING","attributes":{"orders.job.run_id":"orders.reconcile-2026-09-17T10:05:00Z","orders.tenant.id":"-","orders.unit.type":"job"},"trace_id":null,"span_id":null,"resource":{"service.name":"orders-api","service.version":"2.14.0","deployment.environment":"production"}}
```

## 11. What Kibana shows

Screen names are from `backends/elastic/kibana-screens.md`; read it for the
exact path and the fields each screen groups by.

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
