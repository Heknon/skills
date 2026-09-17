# Log structure

**Verdict you produce:** for each log line, the exact message template, its
level, and the exact field names it carries. It goes into the *Logs* table of
`vocabulary.md`.

A log line is a JSON object with fixed keys. The sentence in `message` is the
same every time; everything that varies is a field. Kibana groups, filters
and counts by fields. It cannot do any of that with a value baked into a
sentence.

## Questions

1. **Is there a value inside the sentence?** An id, a name, a number, a path.
   Yes: move it to a field and put the fixed part back. `entity create failed`
   with `labels.entity_definition`, never `tank-7 create failed`.
2. **Does an ECS field exist for it?** Use that name, exactly:

   | Field | Type | Holds |
   | --- | --- | --- |
   | `@timestamp` | date | ISO 8601 UTC with `Z` |
   | `message` | text | the template sentence |
   | `log.level` | keyword | `DEBUG`, `INFO`, `WARN`, `ERROR`, see `logs/levels.md` |
   | `log.logger` | keyword | the Python logger name |
   | `error.type` | keyword | exception class name |
   | `error.message` | match_only_text | `str(exception)` |
   | `error.stack_trace` | wildcard | formatted traceback |
   | `trace.id`, `span.id` | keyword | 32 and 16 hex characters, only inside a span |
   | `service.name`, `service.version`, `service.environment` | keyword | the resource values; note `service.environment`, not `deployment.environment` |
   | `host.name`, `process.pid` | keyword, long | where it ran |
   | `ecs.version` | keyword | `8.11.0` |

3. **Is it a correlation key or a domain value with no ECS field?** Write it
   under `labels.` using the **backend spelling** column of the vocabulary:
   `labels.cycle_id`, `labels.environment_id`, `labels.entity_definition`.
   Nothing rewrites a line that Filebeat ships, so the line itself must carry
   the spelling that spans end up with after APM Server rewrites their dots to
   underscores. One field name across traces and logs, or correlation is a
   dead end.
4. **Is the value a number you will aggregate?** Then it is not a label.
   Give it its own field with a fixed name and type in the vocabulary, such as
   `sahara.tests.collected` as a long. Never put a number in `labels.`.
5. **Is the value a dictionary or a list whose keys you do not control?**
   One string field holding JSON. Never spread its keys. Invariant 11.

## Where the line goes

Write one JSON object per line to `stdout`, or to a file, through the
formatter in `recipes/python_logging_setup.py`. Never `print`: no level, no
timestamp, no fields, and pytest captures it per test. Elasticsearch expands
dotted keys such as `"log.level"` into objects on its own, so the line is
flat.

Ship the file or the container stream with Filebeat or Elastic Agent and
parse it as JSON. Filebeat `filestream` input:

```yaml
filebeat.inputs:
  - type: filestream
    id: sahara-runner
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

The other path, OTLP logs through the SDK's `LoggingHandler`, produces the same
fields from the same records; `logs/trace-correlation.md` says when to use it.

## Verdict

```
| entity create failed | ERROR | labels.cycle_id, labels.environment_id, labels.entity_definition, error.type, error.message, error.stack_trace | yes |
```

## Never

- Never format a value into `message`. Not with f-strings, not with `%s`.
- Never use `print`, `sys.stdout.write` or `warnings.warn` for anything a
  person should find later.
- Never invent a field name when ECS has one. `error.stack_trace`, not
  `traceback`; `log.level`, not `severity`.
- Never write the OTel spelling `cycle.id` into a shipped line. That spelling
  reaches the index only when APM Server rewrites it, and Filebeat does not.
- Never send the same field as a string in one line and a number in another.
- Never log secrets, tokens, or customer payloads.

## Stop and ask

- The message template would need more than five placeholders. That is
  probably several lines, or a span.
- A field is wanted that ECS names differently than the vocabulary does.
- The shipper is neither Filebeat nor Elastic Agent nor OTLP.

## Examples

| Raw line someone wrote | Template | Fields |
| --- | --- | --- |
| `f"cycle {cycle_id} started with {n} workers"` | `cycle started` | `labels.cycle_id`, `sahara.workers.count` |
| `f"could not load {path}: {exception}"` | `configuration load failed` | `file.path`, `error.type`, `error.message`, `error.stack_trace` |
| `"tank-7 create failed"` | `entity create failed` | `labels.entity_definition`, `labels.entity_id` |
| `print("done")` | `cycle finished` | `labels.cycle_id`, `sahara.tests.passed`, `sahara.tests.failed` |

## Other backends

The field names above are ECS, which is what Elastic indexes. Loki keeps a
small set of stream labels and puts the rest, including `trace_id` and
`span_id`, in structured metadata. VictoriaLogs stores every field by name
with `_msg`, `_time` and `_stream` as the fixed ones. Emit the same line
either way and let `backends/<backend>/mapping.md` say what it becomes.
