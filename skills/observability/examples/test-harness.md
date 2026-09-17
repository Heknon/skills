# Worked example: pytest harness with environments and entities

Follow this when the system is a test runner. Copy the section order and the
verdict formats. Change the names, not the shape.

## 1. The system, in ten lines

`sahara-harness` is a pytest plugin. A *cycle* is one run of the whole suite:
a controller process starts pytest with xdist, and each xdist worker `gw0`,
`gw1`, ... runs its own pytest session. Before the workers start, the
controller assigns each worker an *environment*, a lab setup with an id such
as `env-eu1-07`; the environment exists before the worker and after it. Tests
create *entities* in the environment. An entity has a customer-defined
*definition*, `tank`, `valve`, and a controller class with methods such as
`fill`. The harness offers `create`, `tag`, `revert` and `destroy`; a
controller method may call the product's HTTP API and polls it until the
operation settles. Entities may be made in session-scoped fixtures and shared
by many tests. Runs in lab `lab-eu1`.

## 2. Unit of work

Facts, from `core/unit-of-work.md`:

1. Many times per run: a test, yes, thousands; a session, once per worker; a
   cycle, once; an entity operation, many.
2. Stable name before it runs: a test, the nodeid with the parametrization
   removed; a session, `session.run`; an entity operation, `entity.create`.
3. Inside one process: a test, yes. A cycle, no.
4. Named when asked what failed: "test_fill_to_level". Not "the fixture",
   not "the create call".
5. Nesting: cycle contains sessions, a session contains tests. Innermost that
   passes question 4 is the test. The session becomes a linked outer root. The
   cycle spans processes and has no span; it is a correlation key.
6. Two candidates that do not nest: no.

```
unit: test
root span name: the nodeid with the parametrization removed, e.g. "tests/tank/test_fill.py::test_fill_to_level"
instance key: test.nodeid_hash
outer roots: session, root span "session.run", own trace, one per worker, linked from each test root
```

## 3. Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | `sahara-harness` |
| service.version | string | resource | service.version | plugin version, e.g. `3.2.0` |
| deployment.environment | string | resource | service.environment | lab name, `lab-eu1` |
| sahara.cycle.id | string | every span, every log | labels.sahara_cycle_id | cycle id from the controller, e.g. `c-2026-09-17-0412` |
| sahara.environment.id | string | every span, every log | labels.sahara_environment_id | environment id assigned to this worker; `-` in the controller before assignment |
| sahara.worker.id | string | every span, every log | labels.sahara_worker_id | xdist worker id `gw0`, `gw1`, ...; `master` in the controller |
| test.nodeid_hash | string | every span except session.run, every log inside a span | labels.test_nodeid_hash | SHA-256 of the full nodeid, lower case hex |

`sahara.worker.id` is a span attribute, not a resource attribute, because
every worker runs the same SDK configuration. It is a correlation key, so it
is never a metric label; the worker count bounds it, but a metric split by
worker is a metric nobody asked for.

## 4. Signal choice

| Fact | Verdict | Reason |
| --- | --- | --- |
| A test ran | span, root | starts, ends, can fail |
| Setup, call, teardown phase | span | a phase with a start and an end |
| A fixture was set up or torn down | span | starts, ends, can fail |
| A session ran | span, outer root | starts, ends, once per worker |
| Entity created, tagged, reverted, destroyed, controller method called | span, CLIENT | a call to another system |
| The controller's HTTP call | span, from the HTTP library | a call to another system |
| Entity operation retried by the harness | span event on the entity span | a moment inside the operation |
| Environment acquired, environment released | log, outside any span | happens before the first test and after the last |
| Cycle started | log, outside any span | happens in the controller before any span |
| Entities alive per definition | metric, updowncounter | a number that goes up and down; the create and destroy spans are its edges, not its value |
| A controller poll finished, and how long it took | metric, counter with `outcome`, and a histogram | dozens of polls inside one controller span; counted, not traced |
| Tests queued for this worker | metric, gauge | a number to chart, no unit around it |
| Test duration, tests per minute, failure rate | derived | test root spans carry them |
| Entity operation latency per definition | derived | the CLIENT spans carry it, grouped by `peer.service` |
| A log line written by test code | log, inside the span | the test author's fact; the harness injects the keys |

## 5. Names

| Raw | Varying part removed | Name | Tier | Varying part goes to |
| --- | --- | --- | --- | --- |
| `tests/tank/test_fill.py::test_fill_to_level[level-42]` | the parametrization | `tests/tank/test_fill.py::test_fill_to_level` | name | `test.parameter_id=level-42`, `test.parameters_json={"level": 42}`, `test.nodeid` |
| `session gw2 of c-2026-09-17-0412` | worker and cycle | `session.run` | name | `sahara.worker.id`, `sahara.cycle.id` |
| `create tank tank-7 in env-eu1-07` | definition, name, environment | `entity.create` | name | `sahara.entity.definition` label, `sahara.entity.id` attribute |
| `tank-7.fill(level=42)` | entity and method | `entity.controller` | name | `sahara.entity.id`, `sahara.entity.controller.method` attributes |
| `revert tank-7 to baseline` | entity and tag | `entity.revert` | name | `sahara.entity.id`, `sahara.entity.tag` attributes |
| `POST https://product.lab-eu1/api/tanks/7/fill` | the URL | `POST`, as the HTTP client library names it | name | `url.full`, `server.address` attributes |
| `live{definition=tank,worker=gw2}` | the worker | `sahara.entities.live` | metric name, one label | none; the worker is a correlation key, not a label |
| `environment env-eu1-07 acquired by gw2` | ids | `environment acquired` | log template | `sahara.environment.id`, `sahara.worker.id` fields |

`sahara.entity.id` is `<environment id>/<entity name>/<generation>`, e.g.
`env-eu1-07/tank-7/1`, and stays the same from create to destroy; a new create
of the same name is generation 2. Customer field values go in one JSON string,
`sahara.entity.fields_json`, never as keys. Test parameters go the same way:
`test.parameter_id` is pytest's id and `test.parameters_json` is the values,
so a parameter named by test code never becomes a key.

## 6. Parent or link decisions

- The test root has no parent. It links to `session.run`, in its own trace,
  with `link.relation=belongs_to`. `session.run` has no parent and no link;
  the cycle has no span.
- `entity.create` in a session-scoped fixture: parent is the `fixture.setup`
  span of the first test that requested the fixture, because that is where
  the code ran. Later tests reach the entity through `sahara.entity.id`.
- `entity.destroy` for that fixture: parent is the `fixture.teardown` span of
  the last test in the session, where pytest tears session fixtures down.
- `entity.revert` links to the `entity.tag` span whose tag it restores, with
  `link.relation=operates_on`. Its parent is where the revert was called.
- The controller's HTTP client span is a child of `entity.controller`, and the
  product API's SERVER span is a child of that client span through
  `traceparent`, in the product's own service. The correlation keys do not
  cross that hop; the trace id does. See `core/context-propagation.md`.
- Environment, from `core/long-lived-things.md`. Option A: a span
  `environment.lease` opened at acquire and closed at release, own trace,
  linked from `session.run`. Option B: no span; `sahara.environment.id` on
  every span and log, and the `environment acquired` and `environment
  released` log lines mark its bounds. Verdict: **B**, because the controller
  acquires the environment before the worker process exists and releases it
  after the worker exits, so no worker can open the span early and close it
  late. Switch to A only if acquire and release move into the worker.

## 7. Service, dependency, attribute decisions

- One service, `sahara-harness`, for the controller and every worker. The
  product API is `product-api`, its owner's service.
- Dependencies: each entity definition, through `peer.service=<definition>`
  on every `entity.*` span. The product API is reached only through the HTTP
  client span's `server.address`.
- Labels: `sahara.entity.definition`, `sahara.entity.operation`,
  `test.outcome`, `test.fixture.scope`, and `outcome` on the poll counter.
  Attributes: entity id, tag, controller method, fields JSON, nodeid, hash,
  parameter id, parameters JSON, fixture name.

## 8. Errors

Status is set by the span wrapper: `OK` on clean exit, `ERROR` with the
exception recorded when the block raised. See `core/errors-and-status.md`.

| Failure | Recorded as |
| --- | --- |
| AssertionError in the call phase | `test.call` status ERROR with `record_exception`; root status ERROR, description `AssertionError: <message>`, `test.outcome=failed` |
| Exception in a fixture | `fixture.setup` ERROR with the exception; `test.setup` ERROR; root ERROR, `test.outcome=error` |
| Skipped | root status OK, `test.outcome=skipped`. The `Skipped` exception is not recorded. |
| Entity operation raised | the `entity.*` span ERROR with the exception; it propagates to the phase and root like any exception |
| Harness retried an entity operation, then it succeeded | `entity.retry` event with `sahara.retry.attempt` and `sahara.retry.reason`; status OK |
| Product API answered 5xx or 4xx to the controller | the HTTP client span is ERROR per its instrumentation, see `core/errors-and-status.md`; `entity.controller` is ERROR only if the controller raised |
| Destroy failed at session end | `entity.destroy` ERROR; the last test's teardown and root are ERROR with `test.outcome=error`, which is what pytest reports too |

## 9. The vocabulary

```markdown
# Vocabulary: sahara-harness

backend: Elastic Stack 8, from backends/README.md
verified against: fill in from the running system on the day you check

## Unit of work

unit: test
root span name: the nodeid with the parametrization removed, e.g. "tests/tank/test_fill.py::test_fill_to_level"
instance key: test.nodeid_hash
outer roots: session, root span "session.run", own trace, one per worker, linked from each test root

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | sahara-harness |
| service.version | string | resource | service.version | plugin version |
| deployment.environment | string | resource | service.environment | lab name |
| sahara.cycle.id | string | every span, every log | labels.sahara_cycle_id | cycle id from the controller |
| sahara.environment.id | string | every span, every log | labels.sahara_environment_id | environment assigned to this worker; - in the controller before assignment |
| sahara.worker.id | string | every span, every log | labels.sahara_worker_id | gw0, gw1, ...; master in the controller |
| test.nodeid_hash | string | every span except session.run, every log inside a span | labels.test_nodeid_hash | SHA-256 of the full nodeid, hex |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute | Fails when |
| --- | --- | --- | --- | --- | --- |
| tests/*::test_* | INTERNAL | yes | test.nodeid, test.nodeid_hash, test.parameter_id, test.parameters_json, test.outcome | none | a phase raised; test.outcome is failed or error |
| session.run | INTERNAL | yes | sahara.session.tests | none | the worker did not reach session finish |
| test.setup | INTERNAL | no | none | none | a fixture raised |
| test.call | INTERNAL | no | none | none | the test body raised |
| test.teardown | INTERNAL | no | none | none | a fixture finalizer raised |
| fixture.setup | INTERNAL | no | test.fixture.name, test.fixture.scope | none | the fixture function raised |
| fixture.teardown | INTERNAL | no | test.fixture.name, test.fixture.scope | none | the finalizer raised |
| entity.create | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.fields_json | peer.service | the create raised after its retries |
| entity.tag | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service | the tag raised |
| entity.revert | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service | the revert raised |
| entity.destroy | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id | peer.service | the destroy raised |
| entity.controller | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.controller.method | peer.service | the controller method raised |
| POST | CLIENT | no | http.request.method, url.full, server.address, http.response.status_code | server.address | the HTTP client instrumentation set ERROR |
| GET | CLIENT | no | http.request.method, url.full, server.address, http.response.status_code | server.address | the HTTP client instrumentation set ERROR |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| sahara.entity.definition | string | label | tank, valve | labels.sahara_entity_definition |
| sahara.entity.operation | string | label | create, tag, revert, destroy, controller | labels.sahara_entity_operation |
| peer.service | string | label | tank, valve | span.destination.service.resource |
| test.outcome | string | label | passed, failed, error, skipped, xfailed, xpassed | labels.test_outcome |
| test.fixture.scope | string | label | function, class, module, package, session | labels.test_fixture_scope |
| outcome | string | label | ok, timeout, error | labels.outcome |
| sahara.session.tests | int | attribute | unbounded | labels.sahara_session_tests |
| sahara.entity.id | string | attribute | unbounded | labels.sahara_entity_id |
| sahara.entity.tag | string | attribute | unbounded | labels.sahara_entity_tag |
| sahara.entity.controller.method | string | attribute | unbounded | labels.sahara_entity_controller_method |
| sahara.entity.fields_json | string | attribute | unbounded | labels.sahara_entity_fields_json |
| sahara.retry.attempt | int | attribute | unbounded | labels.sahara_retry_attempt |
| sahara.retry.reason | string | attribute | unbounded | labels.sahara_retry_reason |
| test.nodeid | string | attribute | unbounded | labels.test_nodeid |
| test.nodeid_hash | string | attribute | unbounded | labels.test_nodeid_hash |
| test.parameter_id | string | attribute | unbounded | labels.test_parameter_id |
| test.parameters_json | string | attribute | unbounded | labels.test_parameters_json |
| test.fixture.name | string | attribute | unbounded | labels.test_fixture_name |
| http.request.method | string | attribute | unbounded | per backends/elastic/mapping.md |
| url.full | string | attribute | unbounded | per backends/elastic/mapping.md |
| server.address | string | attribute | unbounded | per backends/elastic/mapping.md |
| http.response.status_code | int | attribute | unbounded | per backends/elastic/mapping.md |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| exception | any | exception.type, exception.message, exception.stacktrace, exception.escaped |
| entity.retry | entity.create, entity.tag, entity.revert, entity.destroy, entity.controller | sahara.retry.attempt, sahara.retry.reason |

## Links

| From span | To span | link.relation |
| --- | --- | --- |
| tests/*::test_* | session.run | belongs_to |
| entity.revert | entity.tag | operates_on |

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| sahara.entities.live | updowncounter | {entity} | sahara.entity.definition | no |
| sahara.controller.polls | counter | {poll} | sahara.entity.definition, outcome | no |
| sahara.controller.poll.duration | histogram | s | sahara.entity.definition | no |
| sahara.worker.queue.depth | gauge | {test} | (none) | no |
| sahara.tests.duration | none | s | (none) | yes, derived: see backends/<backend>/screens.md |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| cycle started | info | sahara.cycle.id, sahara.environment.id, sahara.worker.id | yes |
| environment acquired | info | sahara.cycle.id, sahara.environment.id, sahara.worker.id | yes |
| environment released | info | sahara.cycle.id, sahara.environment.id, sahara.worker.id | yes |
| {text} | error, warn, info, debug | sahara.cycle.id, sahara.environment.id, sahara.worker.id, test.nodeid_hash, trace.id, span.id | no |

The last row is a line written by test code: any text, at whatever level the
test wrote it. The harness handler adds the fields.

## Boundaries

One hop leaves the process: the HTTP client span into product-api, through
the traceparent header the HTTP client instrumentation injects. The sahara.*
keys do not cross it; the trace id does. Workers never call each other.

## Long lived things

The environment outlives the worker: no span, sahara.environment.id on every
span and log, and the environment acquired and environment released lines
mark its bounds. A session-scoped entity outlives the test that created it:
its create span stays in that test's trace, and later tests reach it by
sahara.entity.id.

## Lanes and time

One process per xdist worker, one SDK each, all on one CI runner; the
controller is a process of its own. sahara.worker.id on every span tells the
lanes apart. sahara.entities.live and sahara.worker.queue.depth are reported
per worker process and summed in the backend.

## Volume

Every test trace is kept: a cycle is thousands of tests, not millions.
sahara.controller.poll.duration buckets: 0.1, 0.5, 2 s; the poll timeout is
5 s, so a timeout lands in the last bucket.

## Forbidden

- `sahara.entity.field.*`, `customer.*`
- test nodeids, parametrization ids, entity names, entity ids, environment ids, cycle ids, customer field names and full URLs never appear in a span name, metric name, metric label or log template

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | example author | first version |
| 2026-09-17 | example author | UNVERIFIED: peer.service backend spelling span.destination.service.resource, confirm in backends/elastic/mapping.md |
```

## 10. Golden trace

Every line is what `traces/recipes/python_file_exporter.py` writes for one
span. Status is `OK` on clean exit, `ERROR` where an exception was recorded.

```jsonl
// Session root in its own trace. No parent, no link. One per worker; the cycle is a key on it, not a span above it. Exported when the session ends, after every test trace that links to it.
{"name":"session.run","trace_id":"5e55105e55105e55105e55105e551002","span_id":"5e55000000000001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789646400000000000,"end_time_unix_nano":1789650012000000000,"status":{"code":"OK","description":null},"attributes":{"sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2","sahara.session.tests":412},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Test root, own trace. Name is the nodeid without parametrization; the link points at the session span above with link.relation=belongs_to. ERROR because the call phase failed.
{"name":"tests/tank/test_fill.py::test_fill_to_level","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789646530000000000,"end_time_unix_nano":1789646533900000000,"status":{"code":"ERROR","description":"AssertionError: level is 40, expected 42"},"attributes":{"test.nodeid":"tests/tank/test_fill.py::test_fill_to_level[level-42]","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","test.parameter_id":"level-42","test.parameters_json":"{\"level\": 42}","test.outcome":"failed","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[{"trace_id":"5e55105e55105e55105e55105e551002","span_id":"5e55000000000001","attributes":{"link.relation":"belongs_to"}}]}
// Setup phase.
{"name":"test.setup","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000002","parent_span_id":"7e57000000000001","kind":"INTERNAL","start_time_unix_nano":1789646530000100000,"end_time_unix_nano":1789646531200000000,"status":{"code":"OK","description":null},"attributes":{"test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Session-scoped fixture, set up here because this test asked for it first. Its span is in this test's trace: that is where the code ran.
{"name":"fixture.setup","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000003","parent_span_id":"7e57000000000002","kind":"INTERNAL","start_time_unix_nano":1789646530000200000,"end_time_unix_nano":1789646531190000000,"status":{"code":"OK","description":null},"attributes":{"test.fixture.name":"tank","test.fixture.scope":"session","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Entity create. CLIENT with peer.service = definition, so "tank" is a dependency. Customer fields in one JSON string. Entity id is environment/name/generation.
{"name":"entity.create","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000004","parent_span_id":"7e57000000000003","kind":"CLIENT","start_time_unix_nano":1789646530001000000,"end_time_unix_nano":1789646530980000000,"status":{"code":"OK","description":null},"attributes":{"peer.service":"tank","sahara.entity.operation":"create","sahara.entity.definition":"tank","sahara.entity.id":"env-eu1-07/tank-7/1","sahara.entity.fields_json":"{\"capacity\":100,\"medium\":\"water\"}","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Tag right after create. The revert below links to this span.
{"name":"entity.tag","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000005","parent_span_id":"7e57000000000003","kind":"CLIENT","start_time_unix_nano":1789646530990000000,"end_time_unix_nano":1789646531180000000,"status":{"code":"OK","description":null},"attributes":{"peer.service":"tank","sahara.entity.operation":"tag","sahara.entity.definition":"tank","sahara.entity.id":"env-eu1-07/tank-7/1","sahara.entity.tag":"baseline","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Call phase. The AssertionError is recorded here, where it was raised; the root above carries the same status.
{"name":"test.call","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000006","parent_span_id":"7e57000000000001","kind":"INTERNAL","start_time_unix_nano":1789646531200000000,"end_time_unix_nano":1789646533850000000,"status":{"code":"ERROR","description":"AssertionError: level is 40, expected 42"},"attributes":{"test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[{"name":"exception","time_unix_nano":1789646533850000000,"attributes":{"exception.type":"AssertionError","exception.message":"level is 40, expected 42","exception.stacktrace":"Traceback (most recent call last): ...","exception.escaped":"True"}}],"links":[]}
// Controller method. Still CLIENT to the definition; the operation label says controller, the method name is an attribute because customers choose it.
{"name":"entity.controller","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000007","parent_span_id":"7e57000000000006","kind":"CLIENT","start_time_unix_nano":1789646531201000000,"end_time_unix_nano":1789646532400000000,"status":{"code":"OK","description":null},"attributes":{"peer.service":"tank","sahara.entity.operation":"controller","sahara.entity.definition":"tank","sahara.entity.id":"env-eu1-07/tank-7/1","sahara.entity.controller.method":"fill","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// The HTTP client library's span, made by its instrumentation. The span processor still copied the correlation keys onto it.
{"name":"POST","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000008","parent_span_id":"7e57000000000007","kind":"CLIENT","start_time_unix_nano":1789646531205000000,"end_time_unix_nano":1789646532390000000,"status":{"code":"OK","description":null},"attributes":{"http.request.method":"POST","url.full":"https://product.lab-eu1/api/tanks/7/fill","server.address":"product.lab-eu1","http.response.status_code":200,"test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
// Revert, called from the test body. Parent is where it ran; the link is the tag it restores, link.relation=operates_on.
{"name":"entity.revert","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000009","parent_span_id":"7e57000000000006","kind":"CLIENT","start_time_unix_nano":1789646532500000000,"end_time_unix_nano":1789646533700000000,"status":{"code":"OK","description":null},"attributes":{"peer.service":"tank","sahara.entity.operation":"revert","sahara.entity.definition":"tank","sahara.entity.id":"env-eu1-07/tank-7/1","sahara.entity.tag":"baseline","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[{"trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e57000000000005","attributes":{"link.relation":"operates_on"}}]}
// Teardown phase. Nothing to do: the session fixture stays alive for the next test.
{"name":"test.teardown","trace_id":"7e577e577e577e577e577e577e570042","span_id":"7e5700000000000a","parent_span_id":"7e57000000000001","kind":"INTERNAL","start_time_unix_nano":1789646533860000000,"end_time_unix_nano":1789646533890000000,"status":{"code":"OK","description":null},"attributes":{"test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2"},"resource":{"service.name":"sahara-harness","service.version":"3.2.0","deployment.environment":"lab-eu1"},"events":[],"links":[]}
```

Not in this export, because another service wrote it: the product API's own
SERVER span, `POST /api/tanks/{tank_id}/fill`, child of the `POST` span above
through `traceparent`, in the same trace, with resource `service.name`
`product-api`. It carries `http.route` and `url.path` and no `sahara.*` keys:
the keys do not cross the hop, the trace id does.

The golden metric is one OTLP/JSON document, what the collector `file`
exporter writes: the four emitted metrics of the Metrics table, labels only
from the label tier, no worker id, no cycle id, no environment id.

```json
{
  "resourceMetrics": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "sahara-harness"}},
          {"key": "service.version", "value": {"stringValue": "3.2.0"}},
          {"key": "deployment.environment", "value": {"stringValue": "lab-eu1"}}
        ]
      },
      "scopeMetrics": [
        {
          "scope": {"name": "sahara.harness", "version": "3.2.0"},
          "metrics": [
            {
              "name": "sahara.entities.live",
              "unit": "{entity}",
              "sum": {
                "isMonotonic": false,
                "aggregationTemporality": 2,
                "dataPoints": [
                  {"attributes": [{"key": "sahara.entity.definition", "value": {"stringValue": "tank"}}], "startTimeUnixNano": "1789646400000000000", "timeUnixNano": "1789646532000000000", "asInt": "1"}
                ]
              }
            },
            {
              "name": "sahara.controller.polls",
              "unit": "{poll}",
              "sum": {
                "isMonotonic": true,
                "aggregationTemporality": 2,
                "dataPoints": [
                  {"attributes": [{"key": "sahara.entity.definition", "value": {"stringValue": "tank"}}, {"key": "outcome", "value": {"stringValue": "ok"}}], "startTimeUnixNano": "1789646400000000000", "timeUnixNano": "1789646532000000000", "asInt": "6"}
                ]
              }
            },
            {
              "name": "sahara.controller.poll.duration",
              "unit": "s",
              "histogram": {
                "aggregationTemporality": 2,
                "dataPoints": [
                  {"attributes": [{"key": "sahara.entity.definition", "value": {"stringValue": "tank"}}], "startTimeUnixNano": "1789646400000000000", "timeUnixNano": "1789646532000000000", "count": "6", "sum": 1.14, "bucketCounts": ["4", "2", "0", "0"], "explicitBounds": [0.1, 0.5, 2.0]}
                ]
              }
            },
            {
              "name": "sahara.worker.queue.depth",
              "unit": "{test}",
              "gauge": {
                "dataPoints": [
                  {"attributes": [], "timeUnixNano": "1789646532000000000", "asInt": "397"}
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
// Log line from test code, inside test.call. Body is the author's text; the handler added the keys and the trace ids.
{"@timestamp":"2026-09-17T12:02:12.400Z","log.level":"INFO","message":"tank level 40 after fill","ecs.version":"8.11.0","log.logger":"tests.tank.test_fill","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"gw2","test.nodeid_hash":"3f1c9d0e7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d","trace.id":"7e577e577e577e577e577e577e570042","span.id":"7e57000000000006"}
// Log line outside any span, in the controller before the worker exists. This is how option B records the environment's start. No trace.id, no span.id, no test.nodeid_hash.
{"@timestamp":"2026-09-17T11:59:58.000Z","log.level":"INFO","message":"environment acquired","ecs.version":"8.11.0","log.logger":"sahara.harness","sahara.cycle.id":"c-2026-09-17-0412","sahara.environment.id":"env-eu1-07","sahara.worker.id":"master"}
```

## 11. What Kibana shows

This example's backend is Elastic. On another backend the verdicts above do
not change; the screens are in `backends/<backend>/screens.md` and the
differences in `backends/paradigms.md`. Screen names here are from
`backends/elastic/screens.md`; it has the path and the grouping field of
each.

1. Services lists `sahara-harness` and `product-api`; filter on
   `labels.sahara_cycle_id` to see one cycle.
2. Transactions lists one row per nodeid without parametrization, with its
   duration distribution and failure rate across parameters and cycles.
3. Dependencies lists `tank`, `valve` and every other definition, from
   `peer.service` on the `entity.*` spans.
4. The trace waterfall for one test shows setup with create and tag, call with
   the controller span, the `POST`, the `product-api` server span beneath it,
   and the revert; the link opens the session trace.
5. Errors groups the `AssertionError` from `test.call`; Discover finds the
   test's log lines by `trace.id` and the environment lines by
   `labels.sahara_environment_id`.
