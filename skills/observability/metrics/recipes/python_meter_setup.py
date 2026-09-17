"""Metrics setup that mirrors the tracing setup.

Written against opentelemetry-python 1.2x. Every imported name below is in the
public modules of that line: opentelemetry.metrics, opentelemetry.sdk.metrics,
opentelemetry.sdk.metrics.export, opentelemetry.sdk.metrics.view,
opentelemetry.sdk.resources and
opentelemetry.exporter.otlp.proto.http.metric_exporter. Packages:
opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-http.

Rename before use:
  - DEFAULT_SERVICE_NAME: your service.name from vocabulary.md.
  - HISTOGRAM_BOUNDARIES: one entry per histogram in vocabulary.md, keyed by
    the exact metric name. Delete the example key.
  - METER_NAME: the module that owns the instruments, once per project.
Change nothing else the first time.

How to call it, once, at process start, right after configure_tracing():

    from python_meter_setup import configure_metrics
    provider = configure_metrics(
        service_name="sahara-runner",
        service_version="1.4.0",
        deployment_environment="ci",
        console=False,
    )

Endpoint and credentials come from the environment, read by the exporter:
    OTEL_EXPORTER_OTLP_ENDPOINT=https://<apm-server-host>:8200
    OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <secret token>
or  OTEL_EXPORTER_OTLP_HEADERS=Authorization=ApiKey <api key>
The metrics path v1/metrics is appended by the exporter. OTEL_METRIC_EXPORT_INTERVAL
defaults to 60000 milliseconds when export_interval_millis is None.
"""

from __future__ import annotations

import atexit
import os
from typing import Mapping, Sequence

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    ConsoleMetricExporter,
    MetricReader,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource

DEFAULT_SERVICE_NAME = "sahara-runner"
METER_NAME = "sahara.instruments"

# Boundaries in seconds, for durations between 5 ms and 10 minutes.
# See metrics/units-and-buckets.md before changing them.
DURATION_BOUNDARIES_SECONDS: Sequence[float] = (
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
    1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0,
)

# Exact metric name from vocabulary.md -> boundaries. One View is built per entry.
HISTOGRAM_BOUNDARIES: Mapping[str, Sequence[float]] = {
    "sahara.controller.poll.duration": DURATION_BOUNDARIES_SECONDS,
}

# Elastic APM Server accepts histograms only with delta temporality. This is
# the table the exporter builds itself for
# OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta. Setting it in code
# means the environment cannot silently turn it back to cumulative.
DELTA_TEMPORALITY: Mapping[type, AggregationTemporality] = {
    Counter: AggregationTemporality.DELTA,
    ObservableCounter: AggregationTemporality.DELTA,
    Histogram: AggregationTemporality.DELTA,
    UpDownCounter: AggregationTemporality.CUMULATIVE,
    ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
    ObservableGauge: AggregationTemporality.CUMULATIVE,
}


def build_resource(
    service_name: str,
    service_version: str,
    deployment_environment: str,
) -> Resource:
    """Same three resource attributes as the tracing setup, same strings.

    Resource.create merges OTEL_RESOURCE_ATTRIBUTES and OTEL_SERVICE_NAME from
    the environment, so the tracing and metrics resources agree when both are
    built this way. Prefer passing the tracing setup's Resource object to
    configure_metrics(resource=...) so there is exactly one.
    """
    return Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": deployment_environment,
        }
    )


def build_views(boundaries_by_metric: Mapping[str, Sequence[float]]) -> list[View]:
    """One View per histogram in the vocabulary, installing its boundaries."""
    views: list[View] = []
    for metric_name, boundaries in boundaries_by_metric.items():
        views.append(
            View(
                instrument_name=metric_name,
                aggregation=ExplicitBucketHistogramAggregation(boundaries=tuple(boundaries)),
            )
        )
    return views


def configure_metrics(
    service_name: str = DEFAULT_SERVICE_NAME,
    service_version: str = "0.0.0",
    deployment_environment: str = "development",
    resource: Resource | None = None,
    endpoint: str | None = None,
    headers: Mapping[str, str] | None = None,
    export_interval_millis: float | None = None,
    console: bool = False,
    boundaries_by_metric: Mapping[str, Sequence[float]] = HISTOGRAM_BOUNDARIES,
) -> MeterProvider:
    """Create the MeterProvider, register it globally and flush it at exit.

    endpoint None: the exporter reads OTEL_EXPORTER_OTLP_METRICS_ENDPOINT, then
    OTEL_EXPORTER_OTLP_ENDPOINT with v1/metrics appended, then
    http://localhost:4318/v1/metrics.
    headers None: the exporter reads OTEL_EXPORTER_OTLP_METRICS_HEADERS, then
    OTEL_EXPORTER_OTLP_HEADERS.
    console True: also print every export to stdout as JSON, for comparing
    with the shape at the bottom of this file. Never leave it on in CI.
    """
    if resource is None:
        resource = build_resource(service_name, service_version, deployment_environment)

    otlp_exporter = OTLPMetricExporter(
        endpoint=endpoint,
        headers=dict(headers) if headers else None,
        preferred_temporality=dict(DELTA_TEMPORALITY),
    )
    readers: list[MetricReader] = [
        PeriodicExportingMetricReader(
            otlp_exporter,
            export_interval_millis=export_interval_millis,
        )
    ]
    if console or os.environ.get("SAHARA_METRICS_CONSOLE", "").lower() == "true":
        console_exporter = ConsoleMetricExporter(preferred_temporality=dict(DELTA_TEMPORALITY))
        readers.append(
            PeriodicExportingMetricReader(
                console_exporter,
                export_interval_millis=export_interval_millis,
            )
        )

    provider = MeterProvider(
        metric_readers=readers,
        resource=resource,
        views=build_views(boundaries_by_metric),
    )
    metrics.set_meter_provider(provider)
    # shutdown_on_exit is True by default and registers its own atexit hook.
    # force_flush here makes the last interval leave before a fast exit.
    atexit.register(provider.force_flush)
    return provider


def get_meter() -> metrics.Meter:
    """The one Meter every instrument module uses. Name is fixed per project."""
    return metrics.get_meter(METER_NAME)


if __name__ == "__main__":
    import time

    configured_provider = configure_metrics(console=True, export_interval_millis=1000)
    demonstration_meter = get_meter()
    demonstration_histogram = demonstration_meter.create_histogram(
        "sahara.controller.poll.duration",
        unit="s",
        description="Poll round trip time in seconds",
    )
    demonstration_histogram.record(0.042, {"entity.definition": "tank"})
    time.sleep(1.5)
    configured_provider.shutdown()


# Shape of one export as ConsoleMetricExporter prints it, which is
# MetricsData.to_json(). The OTLP request carries the same tree in protobuf.
# The histogram data point shows the View took effect: explicit_bounds is
# DURATION_BOUNDARIES_SECONDS, and aggregation_temporality 1 is DELTA.
#
# {
#   "resource_metrics": [{
#     "resource": {"attributes": {
#       "service.name": "sahara-runner", "service.version": "0.0.0",
#       "deployment.environment": "development",
#       "telemetry.sdk.language": "python", "telemetry.sdk.name": "opentelemetry",
#       "telemetry.sdk.version": "1.2x.0"}},
#     "scope_metrics": [{
#       "scope": {"name": "sahara.instruments", "version": "", "schema_url": ""},
#       "metrics": [{
#         "name": "sahara.controller.poll.duration",
#         "description": "Poll round trip time in seconds",
#         "unit": "s",
#         "data": {
#           "data_points": [{
#             "attributes": {"entity.definition": "tank"},
#             "start_time_unix_nano": 1789000000000000000,
#             "time_unix_nano": 1789000001000000000,
#             "count": 1, "sum": 0.042, "min": 0.042, "max": 0.042,
#             "bucket_counts": [0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
#             "explicit_bounds": [0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0,2.5,5.0,10.0,30.0,60.0,120.0,300.0,600.0]
#           }],
#           "aggregation_temporality": 1
#         }
#       }]
#     }]
#   }]
# }
#
# What Elastic 8.x writes for it, in metrics-apm.app.sahara_runner-default:
#   "metricset.name": "app"
#   "sahara.controller.poll.duration": {"values": [0.0375], "counts": [1]}
#   "labels": {"entity.definition": "tank"}     spelling UNVERIFIED, see labels.md
#   "service.name": "sahara-runner", "service.environment": "development"
# 0.0375 is the midpoint of the bucket (0.025, 0.05].
