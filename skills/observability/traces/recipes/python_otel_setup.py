"""Tracing setup for one Python process, opentelemetry-python 1.2x.

Written against the documented API of opentelemetry-api, opentelemetry-sdk
and opentelemetry-exporter-otlp-proto-http, 1.2x line. Verified names:
Resource.create, get_aggregated_resources, ProcessResourceDetector,
TracerProvider(sampler=, resource=, span_limits=, shutdown_on_exit=),
SpanProcessor.on_start(span, parent_context=None), BatchSpanProcessor,
SimpleSpanProcessor, ConsoleSpanExporter, ParentBased, TraceIdRatioBased,
SpanLimits, OTLPSpanExporter.

Rename before use:
- nothing in this file. Call configure_tracing once per process with the
  values from vocabulary.md. The service name is the code, not the run.

Environment variables read:
- OTEL_EXPORTER_OTLP_ENDPOINT, by the exporter. The exporter appends
  /v1/traces to it. If OTEL_EXPORTER_OTLP_TRACES_ENDPOINT is set instead, it
  is used as is, with no path appended. Default http://localhost:4318/.
- OTEL_EXPORTER_OTLP_HEADERS, by the exporter, format key=value,key=value.
  For APM Server: OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <token>".
- TRACE_CONSOLE_EXPORT, this recipe's own variable. Set to 1 to also print
  every span to stdout.
- OTEL_RESOURCE_ATTRIBUTES, by Resource.create. Values there win over the
  arguments passed here.

Call configure_tracing in each worker process after it has forked, never
only in the parent. BatchSpanProcessor owns a thread, and a thread does not
survive a fork.
"""

from __future__ import annotations

import os
import socket
from typing import Optional

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import (
    DEPLOYMENT_ENVIRONMENT,
    HOST_NAME,
    PROCESS_PID,
    SERVICE_NAME,
    SERVICE_VERSION,
    ProcessResourceDetector,
    Resource,
    get_aggregated_resources,
)
from opentelemetry.sdk.trace import Span, SpanLimits, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

CONSOLE_EXPORT_VARIABLE = "TRACE_CONSOLE_EXPORT"

# Longest string attribute value kept. A JSON payload attribute is cut here.
MAX_ATTRIBUTE_VALUE_LENGTH = 4096


class CorrelationKeysSpanProcessor(SpanProcessor):
    """Copies the run-level correlation keys onto every span at start.

    The keys come from vocabulary.md, section Correlation keys, row
    "every span". A call site never sets one of these itself.
    """

    def __init__(self, correlation_keys: dict[str, str]) -> None:
        for key, value in correlation_keys.items():
            if not isinstance(value, str):
                raise TypeError(
                    f"correlation key {key!r} must be a str, got {type(value).__name__}"
                )
        self._correlation_keys = dict(correlation_keys)

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        for key, value in self._correlation_keys.items():
            span.set_attribute(key, value)

    def on_end(self, span) -> None:  # noqa: D401 - nothing to do at end
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def build_resource(
    service_name: str,
    service_version: str,
    deployment_environment: str,
) -> Resource:
    """Resource attributes: the deployment, the host and the process."""
    explicit = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            DEPLOYMENT_ENVIRONMENT: deployment_environment,
            HOST_NAME: socket.gethostname(),
            PROCESS_PID: os.getpid(),
        }
    )
    # initial_resource has the highest priority; the detector fills the rest
    # of process.* (executable name, runtime name and version, command).
    return get_aggregated_resources(
        [ProcessResourceDetector()],
        initial_resource=explicit,
    )


def build_span_limits() -> SpanLimits:
    """Explicit limits so a change of SDK default cannot change what arrives."""
    return SpanLimits(
        max_attributes=128,
        max_events=128,
        max_links=128,
        max_event_attributes=128,
        max_link_attributes=128,
        max_attribute_length=MAX_ATTRIBUTE_VALUE_LENGTH,
    )


def configure_tracing(
    service_name: str,
    service_version: str,
    deployment_environment: str,
    correlation_keys: dict[str, str],
    sample_ratio: float = 1.0,
) -> TracerProvider:
    """Install the global TracerProvider for this process and return it.

    sample_ratio applies to root spans only. A child follows its parent's
    decision, local or remote, through ParentBased.
    """
    provider = TracerProvider(
        sampler=ParentBased(TraceIdRatioBased(sample_ratio)),
        resource=build_resource(service_name, service_version, deployment_environment),
        span_limits=build_span_limits(),
        shutdown_on_exit=True,  # registers provider.shutdown with atexit
    )

    # Order matters: on_start processors run in registration order, and the
    # exporter processors only act on_end, so this one may go first.
    provider.add_span_processor(CorrelationKeysSpanProcessor(correlation_keys))

    # OTLPSpanExporter() with no arguments reads the OTEL_EXPORTER_OTLP_*
    # environment variables listed in the module docstring.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    if os.environ.get(CONSOLE_EXPORT_VARIABLE) == "1":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    return provider


def shutdown_tracing(provider: TracerProvider, timeout_millis: int = 30000) -> None:
    """Flush and stop. atexit does this too; call it yourself before os._exit."""
    provider.force_flush(timeout_millis)
    provider.shutdown()


if __name__ == "__main__":
    tracer_provider = configure_tracing(
        service_name="sahara-harness",
        service_version="0.0.0",
        deployment_environment="ci",
        correlation_keys={
            "sahara.cycle.id": "cycle-0001",
            "sahara.environment.id": "environment-a",
            "sahara.worker.id": "gw0",
        },
    )
    tracer = trace.get_tracer("example.instrumentation")
    with tracer.start_as_current_span("example.run"):
        pass
    shutdown_tracing(tracer_provider)

# Shape of data this recipe produces, per span, as the OTLP exporter sends it
# and as recipes/python_file_exporter.py writes it:
#
# resource:   service.name, service.version, deployment.environment,
#             host.name, process.pid, process.executable.name,
#             process.runtime.name, process.runtime.version, process.command,
#             telemetry.sdk.language, telemetry.sdk.name, telemetry.sdk.version
# attributes: every key of correlation_keys, as str, on every span,
#             plus whatever the call site set. The keys are the OTel
#             spelling from vocabulary.md, sahara.cycle.id and so on; the
#             backend does its own renaming, never this file.
#
# What the backend stores each key as is in backends/<backend>/mapping.md.
# On Elastic 8.x: deployment.environment arrives as service.environment;
# sahara.cycle.id as labels.sahara_cycle_id; sahara.environment.id as
# labels.sahara_environment_id; sahara.worker.id as labels.sahara_worker_id.
