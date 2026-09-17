# traces

Procedures and recipes for the `span` verdict of `core/signal-choice.md`.
Target: opentelemetry-python 1.2x sending OTLP to whichever backend `backends/README.md` names. The procedures are backend neutral; each ends with pointers into `backends/<backend>/mapping.md` for the stored shape.

## Files

| File | Answers |
| --- | --- |
| `parent-or-link.md` | which span is the parent and which spans are links |
| `service-dependency-attribute.md` | is this thing a service, a dependency, or an attribute |
| `span-attributes-and-events.md` | attribute or event, allowed types, limits, what the backend renames (`backends/<backend>/mapping.md`) |
| `recipes/python_otel_setup.py` | `configure_tracing(...)`: resource, correlation keys processor, OTLP exporter, sampler, limits, shutdown |
| `recipes/python_span_wrapper.py` | `operation`, `traced`, `exit_span`, `link_to`: spans that fail correctly |
| `recipes/python_http_propagation.py` | `traceparent` over HTTP headers and into a subprocess |
| `recipes/python_file_exporter.py` | one JSON object per span to a file, the shape the checkers read |

## Order for an Instrument task

1. Read `vocabulary.md` in the project. Every name below comes from it.
2. `core/signal-choice.md` said `span`. Confirm the span name is in the
   vocabulary. If not, stop and ask.
3. `parent-or-link.md`: write the parent and the links.
4. `service-dependency-attribute.md`: if the span calls out, write the
   destination attribute. If not, it is `INTERNAL`.
5. `span-attributes-and-events.md`: write each attribute key, type and tier,
   and each event name.
6. If the process has no tracing yet, copy `recipes/python_otel_setup.py`
   and `recipes/python_file_exporter.py` whole.
7. Wrap the code with `recipes/python_span_wrapper.py`. Cross a process or
   an HTTP call only through `recipes/python_http_propagation.py`.
8. Run once with `TRACE_EXPORT_FILE=<path>`, then run the `checks/` script on
   that file and paste its output.

Do not load `metrics/` or `logs/` from here. If a fact turns out not to be a
span, go back to `core/signal-choice.md`.
