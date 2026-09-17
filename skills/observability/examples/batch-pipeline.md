# Worked example: nightly batch pipeline

Follow this when the system runs on a schedule and works through items. Copy
the section order and the verdict formats. Change the names, not the shape.

## 1. The system, in ten lines

`ledger-ingest` runs at 02:00 every night. A coordinator process lists the
object store bucket `ledger-drops` for the day's files, puts each file key on
an in-process queue, and starts a pool of eight worker processes. Each worker
takes a file key, downloads the file, and processes every record in it: a
record has a `record_id`, is validated against a schema, enriched from a
reference table in Postgres, and written to the warehouse with one insert per
record. A record that fails validation is written to a dead-letter prefix in
the same bucket. An operator can stop a run with SIGTERM; in-flight records
finish or abort, queued files are left for the next night. Deployed to
`production` only, on one VM. Each worker is its own process with its own SDK.

## 2. Unit of work

Facts, from `core/unit-of-work.md`:

1. Many times per run: a record, yes, millions; a file, yes, hundreds; the
   run, no, once.
2. Stable name before it runs: record, `record.process`; file,
   `file.process`; the run, `batch.run` once the date is removed.
3. Inside one process: a record, yes; a file, yes; the run, no, it spans the
   coordinator and eight workers.
4. Named when asked what failed: "record 7f31 in yesterday's drop", "the
   accounts file". Not "the insert".
5. Nesting: run contains files, files contain records. The innermost that
   passes question 4 is the record. File and run become linked outer roots.
6. Two candidates that do not nest: no.

```
unit: record
root span name: "record.process"
instance key: ledger.record.id
outer roots: file, root span "file.process", own trace, linked from each record root; batch, root span "batch.run", own trace, linked from each file root
```

## 3. Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | `ledger-ingest` |
| service.version | string | resource | service.version | git tag |
| deployment.environment | string | resource | service.environment | `production` |
| ledger.worker.id | string | resource | labels.ledger_worker_id | `coordinator`, or `worker-0` to `worker-7`, set at process start |
| ledger.batch.id | string | every span, every log | labels.ledger_batch_id | `<date>-<coordinator start unix seconds>`, e.g. `2026-09-17-1789610400` |
| ledger.file.key | string | every span, every log | labels.ledger_file_key | the object key; `-` in the coordinator before a file is chosen |
| ledger.record.id | string | every span, every log | labels.ledger_record_id | `record_id` from the file, record traces only |

The worker id is a resource attribute here because each worker is its own
process with its own SDK and never changes role. A logical worker that shares
a process goes on the span instead, per `core/correlation-keys.md`.

## 4. Signal choice

| Fact | Verdict | Reason |
| --- | --- | --- |
| A record was processed | span, root | starts, ends, can fail |
| A file was processed | span, outer root | starts, ends, contains records |
| The run happened | span, outer root | starts, ends, once |
| Bucket listed, file downloaded, dead letter written | span | calls to another system |
| Reference lookup, warehouse insert | span | calls to another system |
| Validation ran | span | a phase with a start and an end |
| Warehouse insert timed out and was retried | span event on `warehouse.insert` | a moment inside the insert |
| Operator asked for cancellation | span event on `batch.run` | a moment inside the run |
| Files waiting for a worker | metric, gauge | a number to chart, no unit around it |
| Records per second | derived | count of `record.process` roots over time |
| Insert latency per record | derived | `warehouse.insert` spans carry it |
| A record was quarantined | log, inside the span | an audit fact searched by record id after the trace is sampled away |
| A worker process started | log, outside any span | happens before any span in that process |

## 5. Names

| Raw | Varying part removed | Name | Tier | Varying part goes to |
| --- | --- | --- | --- | --- |
| `nightly-2026-09-17` | the date | `batch.run` | name | `ledger.batch.id` attribute |
| `drops/2026-09-17/accounts-03.ndjson` | the key | `file.process` | name | `ledger.file.key` attribute |
| `record 7f31` | the id | `record.process` | name | `ledger.record.id` attribute |
| `GET s3://ledger-drops/drops/.../accounts-03.ndjson` | bucket and key | `object.get` | name | `ledger.object.bucket`, `ledger.object.key` attributes |
| `SELECT * FROM accounts WHERE code = 'A17'` | the literal | `SELECT accounts` | name | `db.statement` attribute |
| `INSERT INTO ledger_staging VALUES (...)` | the values | `warehouse.insert` | name | `ledger.warehouse.table` attribute |
| `queue_depth{file=accounts-03}` | the file | `ledger.queue.depth` | metric name, no file label | none; queue depth is one number |
| `record 7f31 quarantined to dead-letter/...` | id and key | `record quarantined` | log template | `ledger.record.id`, `ledger.dead_letter.key` fields |

Schema version and outcome are labels: the code lists their values. Ids,
keys, byte counts and row counts are attributes.

## 6. Parent or link decisions

- `record.process` has no parent. It links to `file.process`: the file is
  what it belongs to, and a file trace with a million children cannot open.
- `file.process` has no parent. It links to `batch.run`, which is in the
  coordinator process; a link crosses that without propagation.
- `object.put` for a dead letter is a child of the record that failed. It ran
  there and it belongs there.
- `object.list` is a child of `batch.run`. The coordinator does it once.
- `record.validate` is a child of `record.process`, and `SELECT accounts` is a
  child of `record.process`, not of `record.validate`. Validation ended first.

## 7. Service, dependency, attribute decisions

- One service, `ledger-ingest`, for the coordinator and all workers. The role
  is `ledger.worker.id` on the resource, not a second service name.
- Dependencies: object store as `peer.service=object-store`, Postgres as
  `db.system=postgresql`, warehouse as `peer.service=ledger-warehouse`.
- Attributes: record id, file key, object key, byte size, row count,
  dead-letter key, poison and cancelled counts on the batch root.
- Labels: `ledger.record.outcome`, `ledger.file.schema_version`,
  `ledger.batch.outcome`.

## 8. Errors

| Failure | Recorded as |
| --- | --- |
| Poison record, schema violation | `record.validate` status ERROR with `record_exception`; `record.process` status ERROR, description is the message, `ledger.record.outcome=poisoned`. `file.process` and `batch.run` stay UNSET; `ledger.batch.records_poisoned` counts it. |
| Insert timed out once, then succeeded | `warehouse.retry` event on `warehouse.insert`, `ledger.retry.attempt=1`; status UNSET |
| Insert failed all attempts | `warehouse.insert` ERROR with exception; `record.process` ERROR; outcome `failed` is not a value, the record is re-queued and its next attempt is a new trace with the same `ledger.record.id` |
| Duplicate record already in the warehouse | `ledger.record.outcome=skipped_duplicate`, status UNSET. Not an error. |
| Run cancelled midway | `batch.cancel_requested` event on `batch.run` with `ledger.cancel.signal=SIGTERM`; `batch.run` status ERROR, description `cancelled by SIGTERM`, `ledger.batch.outcome=cancelled`; every in-flight `record.process` ends with status ERROR, description `cancelled`, and the `CancelledError` recorded; queued files get no span. |
| Worker crashes | its open spans are lost; `ledger.batch.files_unprocessed` on the batch root counts keys never taken. See `core/errors-and-status.md`. |

## 9. The vocabulary

```markdown
# Vocabulary: ledger-ingest

backend: Elastic Stack 8, from backends/README.md
verified against: fill in from the running system on the day you check

## Unit of work

unit: record
root span name: "record.process"
instance key: ledger.record.id
outer roots: file, root span "file.process", own trace, linked from each record root; batch, root span "batch.run", own trace, linked from each file root

## Correlation keys

| Key | Type | Where | Backend spelling | Value rule |
| --- | --- | --- | --- | --- |
| service.name | string | resource | service.name | ledger-ingest |
| service.version | string | resource | service.version | git tag |
| deployment.environment | string | resource | service.environment | production |
| ledger.worker.id | string | resource | labels.ledger_worker_id | coordinator, worker-0 to worker-7 |
| ledger.batch.id | string | every span, every log | labels.ledger_batch_id | <date>-<coordinator start unix seconds> |
| ledger.file.key | string | every span, every log | labels.ledger_file_key | object key; "-" before a file is chosen |
| ledger.record.id | string | every span, every log | labels.ledger_record_id | record_id from the file; record traces only |

## Spans

| Name | Kind | Root | Required attributes | Destination attribute (CLIENT and PRODUCER only) |
| --- | --- | --- | --- | --- |
| batch.run | INTERNAL | yes | ledger.batch.outcome, ledger.batch.files, ledger.batch.records_poisoned, ledger.batch.files_unprocessed | none |
| file.process | INTERNAL | yes | ledger.file.schema_version, ledger.file.records | none |
| record.process | INTERNAL | yes | ledger.record.outcome | none |
| record.validate | INTERNAL | no | ledger.file.schema_version | none |
| object.list | CLIENT | no | ledger.object.bucket, ledger.object.prefix | peer.service=object-store |
| object.get | CLIENT | no | ledger.object.bucket, ledger.object.key, ledger.object.size_bytes | peer.service=object-store |
| object.put | CLIENT | no | ledger.object.bucket, ledger.object.key, ledger.object.size_bytes | peer.service=object-store |
| SELECT accounts | CLIENT | no | db.statement, db.name | db.system=postgresql |
| warehouse.insert | CLIENT | no | ledger.warehouse.table, ledger.warehouse.attempts | peer.service=ledger-warehouse |

## Span attributes

| Key | Type | Tier | Allowed values | Backend spelling |
| --- | --- | --- | --- | --- |
| ledger.batch.outcome | string | label | completed, cancelled, failed | labels.ledger_batch_outcome |
| ledger.record.outcome | string | label | written, skipped_duplicate, poisoned | labels.ledger_record_outcome |
| ledger.file.schema_version | string | label | v1, v2 | labels.ledger_file_schema_version |
| ledger.batch.id | string | attribute | unbounded | labels.ledger_batch_id |
| ledger.file.key | string | attribute | unbounded | labels.ledger_file_key |
| ledger.record.id | string | attribute | unbounded | labels.ledger_record_id |
| ledger.batch.files | int | attribute | unbounded | labels.ledger_batch_files |
| ledger.batch.records_poisoned | int | attribute | unbounded | labels.ledger_batch_records_poisoned |
| ledger.batch.files_unprocessed | int | attribute | unbounded | labels.ledger_batch_files_unprocessed |
| ledger.file.records | int | attribute | unbounded | labels.ledger_file_records |
| ledger.object.bucket | string | attribute | unbounded | labels.ledger_object_bucket |
| ledger.object.prefix | string | attribute | unbounded | labels.ledger_object_prefix |
| ledger.object.key | string | attribute | unbounded | labels.ledger_object_key |
| ledger.object.size_bytes | int | attribute | unbounded | labels.ledger_object_size_bytes |
| ledger.warehouse.table | string | attribute | unbounded | labels.ledger_warehouse_table |
| ledger.warehouse.attempts | int | attribute | unbounded | labels.ledger_warehouse_attempts |
| ledger.retry.attempt | int | attribute | unbounded | event attribute |
| ledger.cancel.signal | string | label | SIGTERM, SIGINT | event attribute |
| db.system, db.name, db.statement, peer.service | as emitted | attribute | per semantic conventions | per backends/elastic/mapping.md |

## Span events

| Name | On which spans | Attributes |
| --- | --- | --- |
| warehouse.retry | warehouse.insert | ledger.retry.attempt |
| batch.cancel_requested | batch.run | ledger.cancel.signal |

## Metrics

| Name | Instrument | Unit | Labels | Derived by backend instead |
| --- | --- | --- | --- | --- |
| ledger.queue.depth | gauge | {file} | none | no |
| records per second, record failure rate | none | none | none | yes, Transactions screen in backends/elastic/screens.md |
| insert latency, insert failure rate | none | none | none | yes, Dependencies screen in backends/elastic/screens.md |

## Logs

| Message template | Level | Fields | When it is outside any span |
| --- | --- | --- | --- |
| worker started | info | ledger.batch.id, ledger.worker.id | yes |
| record quarantined | warning | ledger.record.id, ledger.file.key, ledger.batch.id, ledger.dead_letter.key, trace.id, span.id | no |

## Forbidden

record ids, file keys, object keys, dates, SQL literals, record payloads, in
any span name, metric name, metric label or log template.

## Changes

| Date | Who | What |
| --- | --- | --- |
| 2026-09-17 | example author | first version |
```

## 10. Golden trace

```jsonl
// Batch root, own trace, in the coordinator. Cancelled midway: ERROR status, cancel event, outcome label. The poison record below does not make it an error.
{"name":"batch.run","trace_id":"b0b0b0b0b0b0b0b0b0b0b0b0b0b0b001","span_id":"b00000000000a001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789610400000000000,"end_time_unix_nano":1789612230000000000,"status":{"code":"ERROR","description":"cancelled by SIGTERM"},"attributes":{"ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"-","ledger.batch.outcome":"cancelled","ledger.batch.files":214,"ledger.batch.records_poisoned":1,"ledger.batch.files_unprocessed":57},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"coordinator"},"events":[{"name":"batch.cancel_requested","time_unix_nano":1789612200000000000,"attributes":{"ledger.cancel.signal":"SIGTERM"}}],"links":[]}
// The one listing call, child of the batch root.
{"name":"object.list","trace_id":"b0b0b0b0b0b0b0b0b0b0b0b0b0b0b001","span_id":"b00000000000a002","parent_span_id":"b00000000000a001","kind":"CLIENT","start_time_unix_nano":1789610400010000000,"end_time_unix_nano":1789610400930000000,"status":{"code":"UNSET","description":null},"attributes":{"peer.service":"object-store","ledger.object.bucket":"ledger-drops","ledger.object.prefix":"drops/2026-09-17/","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"-"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"coordinator"},"events":[],"links":[]}
// File root, own trace, in worker-3. No parent; a link to the batch root. Worker id comes from the resource.
{"name":"file.process","trace_id":"f11ef11ef11ef11ef11ef11ef11ef103","span_id":"f00000000000a003","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789610401000000000,"end_time_unix_nano":1789610470000000000,"status":{"code":"UNSET","description":null},"attributes":{"ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson","ledger.file.schema_version":"v2","ledger.file.records":5000},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[{"trace_id":"b0b0b0b0b0b0b0b0b0b0b0b0b0b0b001","span_id":"b00000000000a001","attributes":{}}]}
// Download, child of the file root.
{"name":"object.get","trace_id":"f11ef11ef11ef11ef11ef11ef11ef103","span_id":"f00000000000a004","parent_span_id":"f00000000000a003","kind":"CLIENT","start_time_unix_nano":1789610401001000000,"end_time_unix_nano":1789610401870000000,"status":{"code":"UNSET","description":null},"attributes":{"peer.service":"object-store","ledger.object.bucket":"ledger-drops","ledger.object.key":"drops/2026-09-17/accounts-03.ndjson","ledger.object.size_bytes":4183920,"ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[]}
// Record unit, a good one. Own trace; link to the file root; instance key on every span in the trace.
{"name":"record.process","trace_id":"7f317f317f317f317f317f317f317f31","span_id":"7f31000000000001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789610402000000000,"end_time_unix_nano":1789610402048000000,"status":{"code":"UNSET","description":null},"attributes":{"ledger.record.id":"7f31","ledger.record.outcome":"written","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[{"trace_id":"f11ef11ef11ef11ef11ef11ef11ef103","span_id":"f00000000000a003","attributes":{}}]}
// Validation phase.
{"name":"record.validate","trace_id":"7f317f317f317f317f317f317f317f31","span_id":"7f31000000000002","parent_span_id":"7f31000000000001","kind":"INTERNAL","start_time_unix_nano":1789610402000100000,"end_time_unix_nano":1789610402000900000,"status":{"code":"UNSET","description":null},"attributes":{"ledger.file.schema_version":"v2","ledger.record.id":"7f31","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[]}
// Reference lookup. Child of the record root, not of validate.
{"name":"SELECT accounts","trace_id":"7f317f317f317f317f317f317f317f31","span_id":"7f31000000000003","parent_span_id":"7f31000000000001","kind":"CLIENT","start_time_unix_nano":1789610402001000000,"end_time_unix_nano":1789610402004000000,"status":{"code":"UNSET","description":null},"attributes":{"db.system":"postgresql","db.name":"reference","db.statement":"SELECT code, name, currency FROM accounts WHERE code = $1","ledger.record.id":"7f31","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[]}
// Warehouse insert. One timeout retried as an event, then success; attempts on the span.
{"name":"warehouse.insert","trace_id":"7f317f317f317f317f317f317f317f31","span_id":"7f31000000000004","parent_span_id":"7f31000000000001","kind":"CLIENT","start_time_unix_nano":1789610402005000000,"end_time_unix_nano":1789610402047000000,"status":{"code":"UNSET","description":null},"attributes":{"peer.service":"ledger-warehouse","ledger.warehouse.table":"ledger_staging","ledger.warehouse.attempts":2,"ledger.record.id":"7f31","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[{"name":"warehouse.retry","time_unix_nano":1789610402025000000,"attributes":{"ledger.retry.attempt":1}}],"links":[]}
// Poison record. ERROR on the record root and the validate span. The file root and the batch root above are not errors.
{"name":"record.process","trace_id":"9c029c029c029c029c029c029c029c02","span_id":"9c02000000000001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789610402050000000,"end_time_unix_nano":1789610402061000000,"status":{"code":"ERROR","description":"SchemaError: field 'amount' is not a number"},"attributes":{"ledger.record.id":"9c02","ledger.record.outcome":"poisoned","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[{"trace_id":"f11ef11ef11ef11ef11ef11ef11ef103","span_id":"f00000000000a003","attributes":{}}]}
// The span the exception was raised in carries record_exception.
{"name":"record.validate","trace_id":"9c029c029c029c029c029c029c029c02","span_id":"9c02000000000002","parent_span_id":"9c02000000000001","kind":"INTERNAL","start_time_unix_nano":1789610402050100000,"end_time_unix_nano":1789610402051000000,"status":{"code":"ERROR","description":"SchemaError: field 'amount' is not a number"},"attributes":{"ledger.file.schema_version":"v2","ledger.record.id":"9c02","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[{"name":"exception","time_unix_nano":1789610402051000000,"attributes":{"exception.type":"ledger.schema.SchemaError","exception.message":"field 'amount' is not a number","exception.stacktrace":"Traceback (most recent call last): ..."}}],"links":[]}
// Dead letter write, child of the poison record. The write itself succeeded.
{"name":"object.put","trace_id":"9c029c029c029c029c029c029c029c02","span_id":"9c02000000000003","parent_span_id":"9c02000000000001","kind":"CLIENT","start_time_unix_nano":1789610402052000000,"end_time_unix_nano":1789610402060000000,"status":{"code":"UNSET","description":null},"attributes":{"peer.service":"object-store","ledger.object.bucket":"ledger-drops","ledger.object.key":"dead-letter/2026-09-17/9c02.json","ledger.object.size_bytes":412,"ledger.record.id":"9c02","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"},"events":[],"links":[]}
// A record in flight when SIGTERM arrived, on worker-5, linked to a file root not shown here. ERROR with the cancellation recorded; no outcome label, because it had none.
{"name":"record.process","trace_id":"e4d3e4d3e4d3e4d3e4d3e4d3e4d3e4d3","span_id":"e4d3000000000001","parent_span_id":null,"kind":"INTERNAL","start_time_unix_nano":1789612199990000000,"end_time_unix_nano":1789612200004000000,"status":{"code":"ERROR","description":"cancelled"},"attributes":{"ledger.record.id":"e4d3","ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"drops/2026-09-17/journal-88.ndjson"},"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-5"},"events":[{"name":"exception","time_unix_nano":1789612200004000000,"attributes":{"exception.type":"asyncio.CancelledError","exception.message":"","exception.stacktrace":"Traceback (most recent call last): ..."}}],"links":[{"trace_id":"a5a5a5a5a5a5a5a5a5a5a5a5a5a5a588","span_id":"a50000000000a088","attributes":{}}]}
```

```jsonl
// Metric data point from the coordinator. Files still queued. No batch id label: a run id is never a metric label.
{"name":"ledger.queue.depth","unit":"{file}","instrument":"gauge","data_points":[{"attributes":{},"time_unix_nano":1789610460000000000,"value":183}],"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"coordinator"}}
```

```jsonl
// Log line inside the poison record's span: the audit fact. trace_id and span_id injected; index-side names are in backends/elastic/mapping.md.
{"body":"record quarantined","severity_text":"WARNING","attributes":{"ledger.record.id":"9c02","ledger.file.key":"drops/2026-09-17/accounts-03.ndjson","ledger.batch.id":"2026-09-17-1789610400","ledger.dead_letter.key":"dead-letter/2026-09-17/9c02.json"},"trace_id":"9c029c029c029c029c029c029c029c02","span_id":"9c02000000000001","resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"}}
// Log line outside any span, at worker start. The batch id is set by the logging filter from the vocabulary module; the worker id is on the resource.
{"body":"worker started","severity_text":"INFO","attributes":{"ledger.batch.id":"2026-09-17-1789610400","ledger.file.key":"-"},"trace_id":null,"span_id":null,"resource":{"service.name":"ledger-ingest","service.version":"0.9.3","deployment.environment":"production","ledger.worker.id":"worker-3"}}
```

## 11. What Kibana shows

Screen names are from `backends/elastic/screens.md`; it has the path
and the grouping field of each.

1. Services lists one service, `ledger-ingest`; filter on
   `labels.ledger_worker_id` to see one worker.
2. Transactions lists `record.process`, `file.process` and `batch.run`;
   the throughput chart of `record.process` is records per second.
3. Dependencies lists `object-store` and `ledger-warehouse` from
   `peer.service`; Postgres appears the way that file says `db.system` exit
   spans appear.
4. The trace waterfall for one record shows validate, lookup, insert with its
   retry event; the link to the file root is how you reach the file trace.
5. Errors groups `SchemaError` by message; Discover finds `record quarantined`
   by `labels.ledger_record_id` and the whole night by `labels.ledger_batch_id`.
