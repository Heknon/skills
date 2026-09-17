# Vocabulary: sahara-harness

backend: Elastic Stack 8
verified against: 8.15 on 2026-09-17

## Unit of work

unit: test
root span name: nodeid without parametrization
instance key: test.nodeid_hash
outer roots: session, root span session.run, own trace, one per worker, linked from each test root

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | sahara-harness |
| service.version | string | resource | service.version | harness package version |
| deployment.environment | string | resource | service.environment | ci |
| sahara.cycle.id | string | every span, every log | labels.sahara_cycle_id | cycle id from the cycle record |
| sahara.environment.id | string | every span, every log | labels.sahara_environment_id | environment id owned by the worker |
| sahara.worker.id | string | every span, every log | labels.sahara_worker_id | xdist worker id, gw0 |
| test.nodeid_hash | string | every span except session.run, every log inside a span | labels.test_nodeid_hash | sha256 hex of the full nodeid |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute | Fails when |
| --- | --- | --- | --- | --- | --- |
| tests/*::test_* | INTERNAL | yes | test.outcome | none | the test failed or errored |
| session.run | INTERNAL | yes | none | none | the session did not finish |
| entity.create | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id | peer.service | the create raised after its retries |
| entity.tag | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service | the tag raised |
| entity.revert | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service | the revert raised |
| entity.destroy | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id | peer.service | the destroy raised |
| entity.controller | CLIENT | no | sahara.entity.operation, sahara.entity.definition, sahara.entity.id, sahara.entity.controller.method | peer.service | the controller method raised |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| sahara.entity.definition | string | label | tank, valve, pump | labels.sahara_entity_definition |
| sahara.entity.operation | string | label | create, tag, revert, destroy, controller | labels.sahara_entity_operation |
| peer.service | string | label | tank, valve, pump | span.destination.service.resource |
| test.outcome | string | label | passed, failed, skipped, error | labels.test_outcome |
| outcome | string | label | ok, timeout, error | labels.outcome |
| sahara.entity.id | string | attribute | unbounded | labels.sahara_entity_id |
| sahara.entity.tag | string | attribute | unbounded | labels.sahara_entity_tag |
| sahara.entity.controller.method | string | attribute | unbounded | labels.sahara_entity_controller_method |
| sahara.entity.fields_json | string | attribute | unbounded | labels.sahara_entity_fields_json |
| sahara.retry.attempt | int | attribute | unbounded | labels.sahara_retry_attempt |
| sahara.retry.reason | string | attribute | unbounded | labels.sahara_retry_reason |
| test.parameter_id | string | attribute | unbounded | labels.test_parameter_id |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| exception | any | exception.type, exception.message, exception.stacktrace, exception.escaped |
| entity.retry | entity.create, entity.tag, entity.revert, entity.destroy, entity.controller | sahara.retry.attempt, sahara.retry.reason |

## Links

| From span | To span | link.relation |
| --- | --- | --- |
| tests/*::test_* | session.run | belongs_to |

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
| plugin loaded configuration {path} | info | config.path | yes |
| worker started | info | sahara.worker.id | yes |
| entity create failed | error | sahara.entity.definition, sahara.entity.id | no |
| entity create retried | warn | sahara.entity.definition, sahara.retry.attempt | no |
| cycle finished | info | sahara.cycle.id, test.count | yes |

## Forbidden

- `customer.*`
- `sahara.entity.field.*`

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | checks fixture | first version |
| 2026-09-17 | checks fixture | UNVERIFIED: peer.service backend spelling span.destination.service.resource, confirm in backends/elastic/mapping.md |
| 2026-09-17 | checks fixture | session root renamed session.run; sahara.entity.operation is a label; links carry link.relation; Metrics table replaced |
