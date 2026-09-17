#!/usr/bin/env python3
"""Judge a metrics export against the invariants and the project's vocabulary.

Usage:
  python3 check_metrics.py --metrics metrics.json [--vocabulary vocabulary.md]
                           [--max-series 1000] [--json]

Input shapes accepted, detected per document:
  1. OTLP/JSON export: {"resourceMetrics": [{"scopeMetrics": [{"metrics": [...]}]}]}
     with sum / gauge / histogram / exponentialHistogram data points and
     attributes as [{key, value: {stringValue|intValue|...}}], one document per
     file or per line. This is what the OTLP file exporter and the collector
     file exporter write.
  2. opentelemetry-python ConsoleMetricExporter output (MetricsData.to_json):
     {"resource_metrics": [{"scope_metrics": [{"metrics": [{"data": {...}}]}]}]}
     with attributes as plain dicts, several pretty printed documents in a row.

Exit code 0 when no rule is FAIL, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_common import (  # noqa: E402
    SKIP,
    WARN,
    Result,
    Vocabulary,
    json_type,
    load_vocabulary,
    looks_unbounded,
    otlp_attributes,
    print_report,
    read_documents,
    skipped,
    verdict,
)

DERIVED_NAME_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("transaction.duration.histogram", re.compile(r"(^|\.)transaction\.duration")),
    ("span.duration / span.self_time", re.compile(r"(^|\.)span\.(duration|self_time)")),
    ("span.destination.service.response_time", re.compile(r"destination\.service\.response_time")),
    ("transaction breakdown", re.compile(r"transaction\.breakdown")),
]
DURATION_SUFFIX = re.compile(r"\.(duration|latency|response_time)$")


@dataclass
class Series:
    attributes: dict[str, Any]


@dataclass
class Metric:
    name: str
    instrument: str  # counter, updowncounter, gauge, histogram, summary, unknown
    unit: str
    description: str
    series: list[Series] = field(default_factory=list)
    resource: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------ loading


def instrument_of(metric: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """(instrument name, data points) from an OTLP or console metric object."""
    if "sum" in metric:
        data = metric["sum"]
        return ("counter" if data.get("isMonotonic") else "updowncounter"), data.get("dataPoints", [])
    if "gauge" in metric:
        return "gauge", metric["gauge"].get("dataPoints", [])
    if "histogram" in metric:
        return "histogram", metric["histogram"].get("dataPoints", [])
    if "exponentialHistogram" in metric:
        return "histogram", metric["exponentialHistogram"].get("dataPoints", [])
    if "summary" in metric:
        return "summary", metric["summary"].get("dataPoints", [])
    data = metric.get("data") or {}
    points = data.get("data_points", [])
    if "is_monotonic" in data:
        return ("counter" if data.get("is_monotonic") else "updowncounter"), points
    if points and ("bucket_counts" in points[0] or "explicit_bounds" in points[0]):
        return "histogram", points
    if points and "positive" in points[0]:
        return "histogram", points
    if "data_points" in data:
        return "gauge", points
    return "unknown", []


def metrics_from_document(document: dict[str, Any]) -> list[Metric]:
    found: list[Metric] = []
    resource_entries = document.get("resourceMetrics") or document.get("resource_metrics") or []
    for resource_entry in resource_entries:
        resource = otlp_attributes((resource_entry.get("resource") or {}).get("attributes"))
        scope_entries = resource_entry.get("scopeMetrics") or resource_entry.get("scope_metrics") or []
        for scope_entry in scope_entries:
            for raw in scope_entry.get("metrics") or []:
                instrument, points = instrument_of(raw)
                metric = Metric(
                    name=str(raw.get("name", "")),
                    instrument=instrument,
                    unit=str(raw.get("unit") or ""),
                    description=str(raw.get("description") or ""),
                    resource=resource,
                )
                for point in points:
                    metric.series.append(Series(attributes=otlp_attributes(point.get("attributes"))))
                found.append(metric)
    return found


def load_metrics(path: str) -> list[Metric]:
    merged: dict[str, Metric] = {}
    for document in read_documents(path):
        if not isinstance(document, dict):
            continue
        for metric in metrics_from_document(document):
            existing = merged.get(metric.name)
            if existing is None:
                merged[metric.name] = metric
            else:
                existing.series.extend(metric.series)
                if existing.instrument != metric.instrument:
                    existing.instrument = f"{existing.instrument}|{metric.instrument}"
    return list(merged.values())


def series_key(attributes: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, repr(value)) for key, value in attributes.items()))


# -------------------------------------------------------------------- rules


def rule_names_in_vocabulary(metrics: list[Metric], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("metrics"):
        return skipped("names-in-vocabulary", "no vocabulary Metrics table")
    offenders = [f"{metric.name!r} is not in the vocabulary Metrics table" for metric in metrics if metric.name not in vocabulary.metrics]
    return verdict("names-in-vocabulary", offenders, note="a metric name that is not in vocabulary.md does not exist; stop and ask before adding one")


def rule_name_shape(metrics: list[Metric]) -> Result:
    offenders: list[str] = []
    for metric in metrics:
        reason = looks_unbounded(metric.name)
        if reason:
            offenders.append(f"{metric.name!r} probably unbounded: contains {reason}")
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)+", metric.name):
            offenders.append(f"{metric.name!r} is not <namespace>.<noun>.<measure> in lower case")
    return verdict("name-shape", offenders, note="metric names are <namespace>.<noun>.<measure>; the unit goes in the instrument, not the name")


def rule_instrument_type(metrics: list[Metric], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("metrics"):
        return skipped("instrument-type", "no vocabulary Metrics table")
    offenders: list[str] = []
    for metric in metrics:
        row = vocabulary.metrics.get(metric.name)
        if row is None:
            continue
        expected = row.instrument.replace(" ", "").replace("-", "").replace("_", "")
        if expected in ("updowncounter",) and metric.instrument == "updowncounter":
            continue
        if expected and metric.instrument != expected:
            offenders.append(f"{metric.name} arrives as {metric.instrument}, vocabulary says {row.instrument}")
    return verdict("instrument-type", offenders, note="sum monotonic is counter, sum non monotonic is updowncounter; gauge and histogram map to themselves")


def rule_unit(metrics: list[Metric], vocabulary: Vocabulary | None) -> Result:
    offenders: list[str] = []
    for metric in metrics:
        if not metric.unit:
            offenders.append(f"{metric.name} has no unit; pass unit=<UCUM> when creating the instrument")
            continue
        row = vocabulary.metrics.get(metric.name) if vocabulary else None
        if row is not None and row.unit and row.unit != metric.unit:
            offenders.append(f"{metric.name} has unit {metric.unit!r}, vocabulary says {row.unit!r}")
    return verdict("unit-present", offenders, note="units are UCUM strings such as s, ms, By, 1, {entity}")


def rule_labels_allowed(metrics: list[Metric], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("metrics"):
        return skipped("labels-allowed", "no vocabulary Metrics table")
    allowed_values = vocabulary.label_keys()
    never_labels = {key for key, _ in vocabulary.keys_on_every_span()}
    offenders: list[str] = []
    for metric in metrics:
        row = vocabulary.metrics.get(metric.name)
        seen: set[str] = set()
        for series in metric.series:
            for key, value in series.attributes.items():
                if row is not None and key not in row.labels:
                    reason = "is a correlation key, never a metric label" if key in never_labels else f"is not in the vocabulary Labels for this metric {row.labels}"
                    item = f"{metric.name} label {key} {reason}"
                    if item not in seen:
                        seen.add(item)
                        offenders.append(item)
                if key in allowed_values and str(value) not in allowed_values[key]:
                    item = f"{metric.name} label {key}={value!r} not in allowed values {allowed_values[key]}"
                    if item not in seen:
                        seen.add(item)
                        offenders.append(item)
    return verdict("labels-allowed", offenders, note="metric labels come only from the label tier and only from the metric's Labels column")


def rule_series_count(metrics: list[Metric], limit: int) -> Result:
    offenders: list[str] = []
    counts: dict[str, int] = {}
    for metric in metrics:
        count = len({series_key(series.attributes) for series in metric.series})
        counts[metric.name] = count
        if count > limit:
            offenders.append(f"{metric.name} has {count} distinct attribute combinations in this file, more than --max-series {limit}")
    note = "series in file: " + ", ".join(f"{name}={count}" for name, count in counts.items())
    return verdict("series-count", offenders, note=note, passing_note=note)


def rule_id_like_values(metrics: list[Metric]) -> Result:
    offenders: list[str] = []
    seen: set[str] = set()
    for metric in metrics:
        for series in metric.series:
            for key, value in series.attributes.items():
                if not isinstance(value, str):
                    continue
                reason = looks_unbounded(value)
                if reason:
                    item = f"{metric.name} label {key}={value!r} looks like an id ({reason}); every distinct value is a time series kept forever"
                    if item not in seen:
                        seen.add(item)
                        offenders.append(item)
    return verdict("id-like-values", offenders)


def rule_label_types(metrics: list[Metric]) -> Result:
    types_by_key: dict[str, set[str]] = defaultdict(set)
    for metric in metrics:
        for series in metric.series:
            for key, value in series.attributes.items():
                types_by_key[key].add(json_type(value))
    offenders = [f"{key} arrives as {' and '.join(sorted(types))}" for key, types in sorted(types_by_key.items()) if len(types) > 1]
    return verdict("label-types", offenders, note="a label key keeps one JSON type across the file")


def rule_derived(metrics: list[Metric], vocabulary: Vocabulary | None) -> Result:
    offenders: list[str] = []
    for metric in metrics:
        row = vocabulary.metrics.get(metric.name) if vocabulary else None
        if row is not None and row.derived:
            offenders.append(f"{metric.name} is derived by the backend ({row.derived}); do not emit it")
            continue
        for label, pattern in DERIVED_NAME_PATTERNS:
            if pattern.search(metric.name):
                offenders.append(f"{metric.name} looks like the Elastic derived metric {label}; do not emit it")
                break
        else:
            if metric.instrument == "histogram" and DURATION_SUFFIX.search(metric.name):
                offenders.append(f"{metric.name} is a duration histogram; if the thing it times has a span the backend already derives it, confirm in metrics/derived-or-emitted.md")
    return verdict("derived-metrics", offenders, failing_status=WARN, note="one fact, one signal: a duration or count of something that has a span is derived from the spans")


# --------------------------------------------------------------------- main


def run(metrics: list[Metric], vocabulary: Vocabulary | None, limit: int) -> list[Result]:
    return [
        rule_names_in_vocabulary(metrics, vocabulary),
        rule_name_shape(metrics),
        rule_instrument_type(metrics, vocabulary),
        rule_unit(metrics, vocabulary),
        rule_labels_allowed(metrics, vocabulary),
        rule_series_count(metrics, limit),
        rule_id_like_values(metrics),
        rule_label_types(metrics),
        rule_derived(metrics, vocabulary),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics", required=True, help="OTLP/JSON metrics export, or console exporter output")
    parser.add_argument("--vocabulary", help="the project's vocabulary.md")
    parser.add_argument("--max-series", type=int, default=1000)
    parser.add_argument("--json", action="store_true", help="machine readable output")
    arguments = parser.parse_args(argv)

    vocabulary = load_vocabulary(arguments.vocabulary)
    metrics = load_metrics(arguments.metrics)
    results = run(metrics, vocabulary, arguments.max_series)
    if vocabulary is None:
        results.insert(0, Result("vocabulary", SKIP, 0, [], "no --vocabulary: skipped names-in-vocabulary, instrument-type, labels-allowed and the vocabulary unit check"))
    instruments = Counter(metric.instrument for metric in metrics)
    summary = {
        "metrics": len(metrics),
        "data_points": sum(len(metric.series) for metric in metrics),
        "instruments": dict(instruments),
        "vocabulary": vocabulary.path if vocabulary else None,
    }
    return print_report("check_metrics", arguments.metrics, summary, results, arguments.json)


if __name__ == "__main__":
    sys.exit(main())
