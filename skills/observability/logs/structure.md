# Log structure

**Verdict you produce:** for each log line, the exact message template, its
level, and the exact field names it carries. It goes into the *Logs* table of
`vocabulary.md`.

A log line is a JSON object with fixed keys. The sentence in `message` is the
same every time; everything that varies is a field. The backend groups,
filters and counts by fields. It cannot do any of that with a value baked
into a sentence.

## Questions

1. **Is there a value inside the sentence?** An id, a name, a number, a path.
   Yes: move it to a field and put the fixed part back. `entity create failed`
   with `sahara.entity.definition`, never `tank-7 create failed`.
2. **Does an ECS field exist for it?** Use that name, exactly:

   | Field | Type | Holds |
   | --- | --- | --- |
   | `@timestamp` | date | ISO 8601 UTC with `Z` |
   | `message` | text | the template sentence |
   | `log.level` | keyword | `ERROR`, `WARN`, `INFO` or `DEBUG` on the shipped line, upper case; the vocabulary table says `error`, `warn`, `info`, `debug`, see `logs/levels.md` |
   | `log.logger` | keyword | the Python logger name |
   | `error.type` | keyword | exception class name |
   | `error.message` | match_only_text | `str(exception)` |
   | `error.stack_trace` | wildcard | formatted traceback |
   | `trace.id`, `span.id` | keyword | 32 and 16 hex characters, only inside a span |
   | `service.name`, `service.version`, `service.environment` | keyword | the resource values; note `service.environment`, not `deployment.environment` |
   | `host.name`, `process.pid` | keyword, long | where it ran |
   | `ecs.version` | keyword | `8.11.0` |

3. **Is it a correlation key or a domain value with no ECS field?** Write it
   under the key the vocabulary gives it, in the OTel spelling, exactly as
   the span carries it: `sahara.cycle.id`, `sahara.environment.id`,
   `sahara.worker.id`, `sahara.entity.definition`, `test.nodeid_hash`. The
   recipe writes that spelling and nothing else. Renaming a key to what the
   index holds is the shipper's or the backend's job, never the line's; the
   result goes in the *Backend spelling* column from
   `backends/<backend>/mapping.md`. One key across traces and logs at the
   point of writing, or correlation is a dead end.
4. **Is the value a number you will aggregate?** Give it its own field with
   a fixed name and type in the vocabulary, such as `sahara.tests.collected`
   as a long. Never send it as a string in one line and a number in another.
5. **Is the value a dictionary or a list whose keys you do not control?**
   One string field holding JSON, its key ending in `_json`. Never spread its
   keys. Invariant 11.

## Where the line goes

Write one JSON object per line to `stdout`, or to a file, through the
formatter in `recipes/python_logging_setup.py`. Never `print`: no level, no
timestamp, no fields, and pytest captures it per test. The line is flat, with
dotted keys such as `"log.level"` and `"sahara.cycle.id"`; a backend that
wants objects expands them itself.

Ship the file or the container stream with the log shipper that
`backends/<backend>/collector.md` names, parsing each line as JSON. The other
path, OTLP logs through the SDK's `LoggingHandler`, produces the same fields
from the same records; `logs/trace-correlation.md` says when to use it.

## On Elastic

Elasticsearch expands dotted keys into objects on its own. Filebeat
`filestream` input:

```yaml
filebeat.inputs:
  - type: filestream
    id: sahara-harness
    paths: ["/var/log/sahara/*.ndjson"]
    parsers:
      - ndjson:
          target: ""
          add_error_key: true
          overwrite_keys: true
```

`target: ""` puts the keys at the top level; `overwrite_keys: true` lets the
line's `@timestamp` and `message` replace Filebeat's own. In Elastic Agent
the same `parsers` block goes into the Custom Logs integration.
UNVERIFIED: the exact name of the advanced YAML field in that integration.

A line shipped this way keeps the field names it carries, while a span's
`sahara.cycle.id` is stored by APM Server as `labels.sahara_cycle_id`
(`backends/elastic/mapping.md`, Labels). Which side is renamed to match, and
where, is a shipper and pipeline decision written in the `backends/elastic/`
folder; the recipe does not pre-empt it by writing the index spelling.

## Other backends

Other backends: the verdicts do not change; the stored shape is in
backends/<backend>/mapping.md and the differences in backends/paradigms.md.

## Verdict

```
| entity create failed | error | sahara.cycle.id, sahara.environment.id, sahara.worker.id, sahara.entity.definition, error.type, error.message, error.stack_trace | yes |
```

## Never

- Never format a value into `message`. Not with f-strings, not with `%s`.
- Never use `print`, `sys.stdout.write` or `warnings.warn` for anything a
  person should find later.
- Never invent a field name when ECS has one. `error.stack_trace`, not
  `traceback`; `log.level`, not `severity`.
- Never write a backend spelling such as `labels.sahara_cycle_id` into a
  shipped line. The line carries the vocabulary key `sahara.cycle.id`; the
  checker and the fixtures read that key, and the shipper owns the rename.
- Never send the same field as a string in one line and a number in another.
- Never log secrets, tokens, or customer payloads.

## Stop and ask

- The message template would need more than five placeholders. That is
  probably several lines, or a span.
- A field is wanted that ECS names differently than the vocabulary does.
- The shipper is not the one `backends/<backend>/collector.md` names, and it
  is not OTLP.

## Examples

| Raw line someone wrote | Template | Fields |
| --- | --- | --- |
| `f"cycle {cycle_id} started with {n} workers"` | `cycle started` | `sahara.cycle.id`, `sahara.workers.count` |
| `f"could not load {path}: {exception}"` | `configuration load failed` | `file.path`, `error.type`, `error.message`, `error.stack_trace` |
| `"tank-7 create failed"` | `entity create failed` | `sahara.entity.definition`, `sahara.entity.id` |
| `print("done")` | `cycle finished` | `sahara.cycle.id`, `sahara.tests.passed`, `sahara.tests.failed` |
