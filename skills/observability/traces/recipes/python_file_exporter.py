"""A SpanExporter that appends one JSON object per span to a file.

The checkers in checks/ read this file. Register it beside the OTLP exporter
so the same spans go to both, then compare the file with what the backend
shows; the stored shape is in backends/<backend>/mapping.md.

Written against the documented API of opentelemetry-sdk 1.2x. Verified
names: SpanExporter.export(spans) -> SpanExportResult, shutdown(),
force_flush(timeout_millis=30000) -> bool; SpanExportResult.SUCCESS and
FAILURE; ReadableSpan.name, .context, .parent, .kind, .start_time,
.end_time, .status, .attributes, .events, .links, .resource;
Event.name, .timestamp, .attributes; Link.context, .attributes;
opentelemetry.trace.format_trace_id, format_span_id.

Rename before use:
- FILE_PATH_VARIABLE if the project already names it. Default variable:
  TRACE_EXPORT_FILE. When it is unset, nothing is registered.

Registration, next to what python_otel_setup.py does:

    from python_file_exporter import add_file_exporter
    provider = configure_tracing(...)
    add_file_exporter(provider)

SimpleSpanProcessor is used on purpose: a span is on disk the moment it
ends, so a checker can run right after the process exits with no flush race.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Mapping, Optional, Sequence

from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace import format_span_id, format_trace_id

FILE_PATH_VARIABLE = "TRACE_EXPORT_FILE"


def _plain(attributes: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """Attributes as a JSON-ready dict. Sequences become lists."""
    result: dict[str, Any] = {}
    for key, value in (attributes or {}).items():
        if isinstance(value, (list, tuple)):
            result[key] = list(value)
        else:
            result[key] = value
    return result


def span_to_record(span: ReadableSpan) -> dict[str, Any]:
    """The exact shape documented at the bottom of this file."""
    span_context = span.get_span_context()
    return {
        "name": span.name,
        "trace_id": format_trace_id(span_context.trace_id),
        "span_id": format_span_id(span_context.span_id),
        "parent_span_id": format_span_id(span.parent.span_id) if span.parent else None,
        "kind": span.kind.name,
        "start_time_unix_nano": span.start_time,
        "end_time_unix_nano": span.end_time,
        "status": {
            "code": span.status.status_code.name,
            "description": span.status.description,
        },
        "attributes": _plain(span.attributes),
        "resource": _plain(span.resource.attributes),
        "events": [
            {
                "name": event.name,
                "time_unix_nano": event.timestamp,
                "attributes": _plain(event.attributes),
            }
            for event in span.events
        ],
        "links": [
            {
                "trace_id": format_trace_id(link.context.trace_id),
                "span_id": format_span_id(link.context.span_id),
                "attributes": _plain(link.attributes),
            }
            for link in span.links
        ],
    }


class JsonLinesSpanExporter(SpanExporter):
    """Appends one line per span. Safe to share between threads."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._closed = False
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if self._closed:
            return SpanExportResult.FAILURE
        lines = [
            json.dumps(span_to_record(span), sort_keys=True, default=str)
            for span in spans
        ]
        try:
            with self._lock:
                with open(self._path, "a", encoding="utf-8") as handle:
                    for line in lines:
                        handle.write(line)
                        handle.write("\n")
        except OSError:
            return SpanExportResult.FAILURE
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        self._closed = True


def add_file_exporter(provider: TracerProvider, path: Optional[str] = None) -> Optional[JsonLinesSpanExporter]:
    """Register the file exporter on provider. Returns None when no path is set."""
    resolved = path or os.environ.get(FILE_PATH_VARIABLE)
    if not resolved:
        return None
    exporter = JsonLinesSpanExporter(resolved)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


if __name__ == "__main__":
    from opentelemetry import trace

    provider = TracerProvider()
    add_file_exporter(provider, os.environ.get(FILE_PATH_VARIABLE, "spans.jsonl"))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("example.instrumentation")
    with tracer.start_as_current_span("example.run"):
        pass
    provider.shutdown()

# Shape of data this recipe produces. One JSON object per line, UTF-8, keys
# sorted, file opened in append mode, one line per ended span:
#
# {
#   "name": "entity.create",
#   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",      32 lower-case hex
#   "span_id": "00f067aa0ba902b7",                       16 lower-case hex
#   "parent_span_id": "53ce929d0e0e4736",                16 hex, or null for a root
#   "kind": "CLIENT",                                    INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER
#   "start_time_unix_nano": 1758067200000000000,         int, nanoseconds since epoch
#   "end_time_unix_nano": 1758067200250000000,           int, or null if never ended
#   "status": {"code": "ERROR", "description": "RuntimeError: controller refused"},
#                                                        code is UNSET, OK or ERROR;
#                                                        description is null unless ERROR
#   "attributes": {"peer.service": "tank", "sahara.entity.definition": "tank",
#                  "sahara.entity.id": "environment-a/tank-7/1",
#                  "sahara.cycle.id": "cycle-0001", "sahara.environment.id": "environment-a",
#                  "sahara.worker.id": "gw0", "test.nodeid_hash": "<64 hex>"},
#                                                        values: str, bool, int, float, or a list of one of those;
#                                                        keys are the OTel spelling, never the backend's
#   "resource": {"service.name": "sahara-harness", "service.version": "1.4.0",
#                "deployment.environment": "ci", "host.name": "runner-3", "process.pid": 4242,
#                "telemetry.sdk.language": "python", "telemetry.sdk.name": "opentelemetry",
#                "telemetry.sdk.version": "1.27.0"},
#   "events": [{"name": "exception", "time_unix_nano": 1758067200240000000,
#               "attributes": {"exception.type": "RuntimeError",
#                              "exception.message": "controller refused",
#                              "exception.stacktrace": "Traceback ...",
#                              "exception.escaped": "False"}}],
#   "links": [{"trace_id": "<32 hex>", "span_id": "<16 hex>",
#              "attributes": {"link.relation": "operates_on"}}]
# }
#
# Every key is always present. Empty attributes, events and links are {} or
# [], never missing. A checker may rely on: trace_id and span_id lengths,
# kind and status.code spellings, and parent_span_id being null exactly for
# root spans.
