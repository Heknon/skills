# Vocabulary: sahara test harness

backend: Elastic Stack 8
verified against: 8.15 on 2026-09-17

## Unit of work

unit: test
root span name: nodeid without parametrization
instance key: test.nodeid_hash
outer roots: session

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | `sahara-harness` |
| service.version | string | resource | service.version | harness package version |
| deployment.environment | string | resource | service.environment | `ci` or `dev` |
| sahara.cycle.id | string | every span, every log | labels.sahara_cycle_id | cycle id from the cycle record |
| sahara.environment.id | string | every span, every log | labels.sahara_environment_id | environment id owned by the worker |
| sahara.worker.id | string | every span, every log | labels.sahara_worker_id | xdist worker id, `gw0` |
| test.nodeid_hash | string | every span except pytest.session, every log inside a span | labels.test_nodeid_hash | sha256 hex of the full nodeid |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute (CLIENT and PRODUCER only) |
| --- | --- | --- | --- | --- |
| tests/*::test_* | INTERNAL | yes | test.outcome | none |
| pytest.session | INTERNAL | yes | none | none |
| entity.create | CLIENT | no | sahara.entity.definition, sahara.entity.id | peer.service |
| entity.tag | CLIENT | no | sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service |
| entity.revert | CLIENT | no | sahara.entity.definition, sahara.entity.id, sahara.entity.tag | peer.service |
| entity.destroy | CLIENT | no | sahara.entity.definition, sahara.entity.id | peer.service |
| entity.controller | CLIENT | no | sahara.entity.definition, sahara.entity.id, sahara.entity.operation | peer.service |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| sahara.entity.definition | string | label | tank, valve, pump | labels.sahara_entity_definition |
| peer.service | string | label | tank, valve, pump | span.destination.service.resource |
| test.outcome | string | label | passed, failed, skipped, error | labels.test_outcome |
| sahara.entity.id | string | attribute | unbounded | labels.sahara_entity_id |
| sahara.entity.tag | string | attribute | unbounded | labels.sahara_entity_tag |
| sahara.entity.operation | string | attribute | unbounded | labels.sahara_entity_operation |
| sahara.retry.attempt | int | attribute | unbounded | labels.sahara_retry_attempt |
| test.parameter_id | string | attribute | unbounded | labels.test_parameter_id |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| exception | any | exception.type, exception.message, exception.stacktrace |
| entity.retry | entity.create, entity.controller | sahara.retry.attempt |

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| sahara.environment.entities | updowncounter | {entity} | sahara.entity.definition | no |
| sahara.worker.heap | gauge | By | none | no |
| sahara.cycle.tests.pending | updowncounter | {test} | none | no |
| sahara.tests.duration | histogram | s | test.outcome | APM Transactions screen, transaction.duration.histogram |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| plugin loaded configuration {path} | info | config.path | yes |
| worker started | info | sahara.worker.id | yes |
| entity create failed | error | sahara.entity.definition, sahara.entity.id | no |
| entity create retried | warning | sahara.entity.definition, sahara.retry.attempt | no |
| cycle finished | info | sahara.cycle.id, test.count | yes |

## Forbidden

- `customer.*`, `test.nodeid`, `url.full`
- `sahara.entity.field.*`

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | checks fixture | first version |
