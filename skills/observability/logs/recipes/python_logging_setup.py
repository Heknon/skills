"""Logging setup: ECS JSON lines with trace correlation, or OTLP logs.

Written against Python 3.11 stdlib logging and opentelemetry-python 1.2x.
Public modules used: opentelemetry.trace, opentelemetry._logs,
opentelemetry.sdk._logs, opentelemetry.sdk._logs.export,
opentelemetry.sdk.resources and
opentelemetry.exporter.otlp.proto.http._log_exporter. The leading underscore
in _logs is how the 1.2x line spells the module. Packages: opentelemetry-api,
opentelemetry-sdk, opentelemetry-exporter-otlp-proto-http. Nothing else.

Two entry points, pick one per process, after the tracing setup:
  configure_logging(...)       JSON lines to stdout or a file; Filebeat or
                               Elastic Agent ships them. Mechanism A in
                               logs/trace-correlation.md.
  configure_logging_otlp(...)  the OpenTelemetry LoggingHandler ships records
                               over OTLP to APM Server. Mechanism C.

Rename before use:
  - CORRELATION_FIELDS: the run level correlation keys from vocabulary.md,
    OTel spelling -> backend spelling. Keep both spellings exactly.
  - DEFAULT_SERVICE_NAME.
  - Replace the CURRENT_CORRELATION_VALUES holder and set_correlation_values
    with an import from your project's vocabulary module, the same one the
    tracing SpanProcessor reads. Until then this module is that holder.
Change nothing else the first time.

Level: environment variable LOG_LEVEL, one of DEBUG INFO WARNING ERROR,
default INFO. Call sites write logger.info("cycle started", extra={...}) with
the template and fields from vocabulary.md; extra keys become fields as is.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import socket
import sys
import traceback
from typing import Any, Mapping, TextIO

from opentelemetry import trace

DEFAULT_SERVICE_NAME = "sahara-runner"
ECS_VERSION = "8.11.0"

# OTel spelling -> field name in the index after APM Server rewrites dots.
# JSON lines are written with the backend spelling directly, because nothing
# rewrites a line that Filebeat ships. OTLP records carry the OTel spelling
# and APM Server rewrites it to the same field.
CORRELATION_FIELDS: Mapping[str, str] = {
    "cycle.id": "labels.cycle_id",
    "environment.id": "labels.environment_id",
}

# Stand in for the project's vocabulary module. Values are strings, always.
CURRENT_CORRELATION_VALUES: dict[str, str] = {}


def set_correlation_values(**values: str) -> None:
    """Set the run level keys once, when they become known. OTel spelling, double underscore for dot."""
    for key, value in values.items():
        dotted_key = key.replace("__", ".")
        if dotted_key not in CORRELATION_FIELDS:
            raise ValueError(f"{dotted_key!r} is not a correlation key in the vocabulary")
        if not isinstance(value, str):
            raise TypeError(f"correlation key {dotted_key!r} must be a str")
        CURRENT_CORRELATION_VALUES[dotted_key] = value


# Attributes every LogRecord has. Anything else on a record came from extra=
# or from a filter, and becomes a field.
STANDARD_RECORD_ATTRIBUTES = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
        "levelname", "levelno", "lineno", "message", "module", "msecs", "msg", "name",
        "pathname", "process", "processName", "relativeCreated", "stack_info", "thread",
        "threadName", "taskName",
    }
)

# LoggingInstrumentor attributes, mechanism B, translated when present.
INSTRUMENTOR_ATTRIBUTES = {"otelTraceID": "trace.id", "otelSpanID": "span.id"}
INSTRUMENTOR_IGNORED = {"otelServiceName", "otelTraceSampled"}

LEVEL_NAMES = {"WARNING": "WARN", "CRITICAL": "FATAL"}


class CorrelationFilter(logging.Filter):
    """Copies trace context and the run level keys onto every record.

    include_trace_context False for the OTLP handler, which reads the current
    span itself; True for the JSON formatter path.
    """

    def __init__(self, include_trace_context: bool, use_backend_spelling: bool) -> None:
        super().__init__()
        self.include_trace_context = include_trace_context
        self.use_backend_spelling = use_backend_spelling

    def filter(self, record: logging.LogRecord) -> bool:
        for otel_key, backend_key in CORRELATION_FIELDS.items():
            value = CURRENT_CORRELATION_VALUES.get(otel_key)
            if value is not None:
                record.__dict__[backend_key if self.use_backend_spelling else otel_key] = value
        if self.include_trace_context:
            span_context = trace.get_current_span().get_span_context()
            if span_context.is_valid:
                record.__dict__["trace.id"] = format(span_context.trace_id, "032x")
                record.__dict__["span.id"] = format(span_context.span_id, "016x")
        return True


class EcsJsonFormatter(logging.Formatter):
    """One JSON object per line with ECS field names, flat dotted keys."""

    def __init__(self, service_name: str, service_version: str, deployment_environment: str) -> None:
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.deployment_environment = deployment_environment
        self.host_name = socket.gethostname()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        document: dict[str, Any] = {
            "@timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "log.level": LEVEL_NAMES.get(record.levelname, record.levelname),
            "message": record.getMessage(),
            "log.logger": record.name,
            "ecs.version": ECS_VERSION,
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.environment": self.deployment_environment,
            "host.name": self.host_name,
            "process.pid": record.process,
        }
        for key, value in record.__dict__.items():
            if key in STANDARD_RECORD_ATTRIBUTES or key in INSTRUMENTOR_IGNORED:
                continue
            if key in INSTRUMENTOR_ATTRIBUTES:
                if value not in ("0", "", None) and INSTRUMENTOR_ATTRIBUTES[key] not in document:
                    document[INSTRUMENTOR_ATTRIBUTES[key]] = value
                continue
            document[key] = value if isinstance(value, (str, int, float, bool)) or value is None else str(value)
        if record.exc_info and record.exc_info[0] is not None:
            exception_type, exception_value, exception_traceback = record.exc_info
            document["error.type"] = exception_type.__name__
            document["error.message"] = str(exception_value)
            document["error.stack_trace"] = "".join(
                traceback.format_exception(exception_type, exception_value, exception_traceback)
            )
        return json.dumps(document, ensure_ascii=False, default=str)


def level_from_environment(default: str = "INFO") -> int:
    name = os.environ.get("LOG_LEVEL", default).strip().upper()
    if name not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        name = default
    return logging.getLevelName(name)


def _reset_root_handlers() -> logging.Logger:
    root_logger = logging.getLogger()
    for existing_handler in list(root_logger.handlers):
        root_logger.removeHandler(existing_handler)
    return root_logger


def configure_logging(
    service_name: str = DEFAULT_SERVICE_NAME,
    service_version: str = "0.0.0",
    deployment_environment: str = "development",
    stream: TextIO | None = None,
    file_path: str | None = None,
) -> logging.Logger:
    """JSON lines to stream, default stdout, or to file_path. Returns the root logger."""
    root_logger = _reset_root_handlers()
    handler: logging.Handler
    if file_path is not None:
        handler = logging.FileHandler(file_path, encoding="utf-8")
    else:
        handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(EcsJsonFormatter(service_name, service_version, deployment_environment))
    handler.addFilter(CorrelationFilter(include_trace_context=True, use_backend_spelling=True))
    root_logger.addHandler(handler)
    root_logger.setLevel(level_from_environment())
    logging.captureWarnings(True)
    return root_logger


def configure_logging_otlp(
    resource: Any,
    endpoint: str | None = None,
    headers: Mapping[str, str] | None = None,
) -> logging.Logger:
    """Ship records over OTLP. resource is the tracing setup's Resource object.

    endpoint None: the exporter reads OTEL_EXPORTER_OTLP_LOGS_ENDPOINT, then
    OTEL_EXPORTER_OTLP_ENDPOINT with v1/logs appended. headers None: it reads
    OTEL_EXPORTER_OTLP_LOGS_HEADERS then OTEL_EXPORTER_OTLP_HEADERS.
    """
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    exporter = OTLPLogExporter(endpoint=endpoint, headers=dict(headers) if headers else None)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    root_logger = _reset_root_handlers()
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    handler.addFilter(CorrelationFilter(include_trace_context=False, use_backend_spelling=False))
    root_logger.addHandler(handler)
    root_logger.setLevel(level_from_environment())
    # Keep the SDK's own loggers away from the OTLP handler.
    logging.getLogger("opentelemetry").propagate = False
    return root_logger


if __name__ == "__main__":
    configure_logging(service_name="sahara-runner", service_version="1.4.0", deployment_environment="ci")
    set_correlation_values(cycle__id="c-20260917-01", environment__id="env-3")
    demonstration_logger = logging.getLogger("sahara.runner")
    demonstration_logger.info("cycle started", extra={"sahara.workers.count": 8})
    with trace.get_tracer("demonstration").start_as_current_span("entity.create"):
        demonstration_logger.debug("entity create failed", extra={"labels.entity_definition": "tank"})
    try:
        open("/nonexistent/sahara.toml", encoding="utf-8")
    except OSError:
        demonstration_logger.error("configuration load failed", exc_info=True, extra={"file.path": "/nonexistent/sahara.toml"})


# One line as shipped by configure_logging, inside a span with the run level
# keys set. Written on one line; broken here to read. The `debug` line above
# only appears with LOG_LEVEL=DEBUG. Without a tracer provider configured the
# span context is invalid and trace.id and span.id are absent, which is
# correct.
#
# {"@timestamp": "2026-09-17T10:15:32.123Z", "log.level": "INFO",
#  "message": "cycle started", "log.logger": "sahara.runner",
#  "ecs.version": "8.11.0", "service.name": "sahara-runner",
#  "service.version": "1.4.0", "service.environment": "ci",
#  "host.name": "runner-07", "process.pid": 4242,
#  "labels.cycle_id": "c-20260917-01", "labels.environment_id": "env-3",
#  "sahara.workers.count": 8,
#  "trace.id": "4bf92f3577b34da6a3ce929d0e0e4736", "span.id": "00f067aa0ba902b7"}
#
# The error line adds:
#  "error.type": "FileNotFoundError",
#  "error.message": "[Errno 2] No such file or directory: '/nonexistent/sahara.toml'",
#  "error.stack_trace": "Traceback (most recent call last):\n  ...",
#  "file.path": "/nonexistent/sahara.toml"
#
# The same record through configure_logging_otlp lands in
# logs-apm.app.sahara_runner-<namespace> as:
#  "message": "cycle started", "log.level": "INFO", "event.severity": 9,
#  "trace.id": ..., "span.id": ..., "service.name": "sahara-runner",
#  "labels": {"cycle_id": "c-20260917-01", "environment_id": "env-3",
#             "code_file_path": "...", "code_function_name": "<module>"},
#  "numeric_labels": {"sahara_workers_count": 8, "code_line_number": 212}
# and the error record becomes an error document in logs-apm.error-<namespace>.
