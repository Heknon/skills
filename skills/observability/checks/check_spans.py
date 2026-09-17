#!/usr/bin/env python3
"""Judge a span export against the invariants and the project's vocabulary.

Usage:
  python3 check_spans.py --spans spans.jsonl [--vocabulary vocabulary.md]
                         [--max-name-cardinality 200] [--time-tolerance-ms 1]
                         [--json]

Input shapes accepted, detected per document:
  1. JSON Lines written by traces/recipes/python_file_exporter.py
     (name, trace_id, span_id, parent_span_id, kind, start_time_unix_nano, ...).
  2. OTLP/JSON export: {"resourceSpans": [{"scopeSpans": [{"spans": [...]}]}]}
     with attributes as [{key, value: {stringValue|intValue|...}}], one
     document per file or per line.
  3. opentelemetry-python ConsoleSpanExporter output (ReadableSpan.to_json):
     {"name", "context": {"trace_id": "0x..."}, "kind": "SpanKind.INTERNAL", ...}.

Exit code 0 when no rule is FAIL, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_common import (  # noqa: E402
    FAIL,
    INFO,
    SKIP,
    WARN,
    Result,
    Vocabulary,
    is_hex_id,
    is_known_dotted_key,
    json_type,
    load_vocabulary,
    looks_unbounded,
    optional_int,
    otlp_attributes,
    print_report,
    read_documents,
    skipped,
    verdict,
)

SPAN_KINDS = {0: "UNSPECIFIED", 1: "INTERNAL", 2: "SERVER", 3: "CLIENT", 4: "PRODUCER", 5: "CONSUMER"}
STATUS_CODES = {0: "UNSET", 1: "OK", 2: "ERROR"}
EXIT_KINDS = ("CLIENT", "PRODUCER")
DESTINATION_ATTRIBUTES = ("peer.service", "db.system", "messaging.system", "server.address")
MAX_ATTRIBUTES_PER_SPAN = 128


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    kind: str
    start: int | None
    end: int | None
    status_code: str
    status_description: str | None
    attributes: dict[str, Any]
    resource: dict[str, Any]
    events: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)

    def label(self) -> str:
        return f"{self.name} (span {self.span_id})"


# ------------------------------------------------------------------ loading


def normalize_kind(value: Any) -> str:
    if isinstance(value, int):
        return SPAN_KINDS.get(value, "UNSPECIFIED")
    text = str(value or "").upper()
    text = text.replace("SPAN_KIND_", "").replace("SPANKIND.", "")
    return text or "UNSPECIFIED"


def normalize_status_code(value: Any) -> str:
    if isinstance(value, int):
        return STATUS_CODES.get(value, "UNSET")
    text = str(value or "").upper()
    text = text.replace("STATUS_CODE_", "").replace("STATUSCODE.", "")
    return text or "UNSET"


def strip_hex_prefix(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value)
    if text.startswith("0x"):
        text = text[2:]
    return text


def iso_to_nanoseconds(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.timestamp() * 1_000_000_000)


def span_from_native(document: dict[str, Any]) -> Span:
    status = document.get("status") or {}
    return Span(
        name=str(document.get("name", "")),
        trace_id=str(document.get("trace_id", "")),
        span_id=str(document.get("span_id", "")),
        parent_span_id=document.get("parent_span_id") or None,
        kind=normalize_kind(document.get("kind")),
        start=optional_int(document.get("start_time_unix_nano")),
        end=optional_int(document.get("end_time_unix_nano")),
        status_code=normalize_status_code(status.get("code")),
        status_description=status.get("description"),
        attributes=dict(document.get("attributes") or {}),
        resource=dict(document.get("resource") or {}),
        events=[
            {"name": event.get("name"), "time_unix_nano": optional_int(event.get("time_unix_nano")), "attributes": dict(event.get("attributes") or {})}
            for event in document.get("events") or []
        ],
        links=[
            {"trace_id": link.get("trace_id"), "span_id": link.get("span_id"), "attributes": dict(link.get("attributes") or {})}
            for link in document.get("links") or []
        ],
    )


def span_from_otlp(document: dict[str, Any], resource: dict[str, Any]) -> Span:
    status = document.get("status") or {}
    return Span(
        name=str(document.get("name", "")),
        trace_id=str(document.get("traceId", "")),
        span_id=str(document.get("spanId", "")),
        parent_span_id=document.get("parentSpanId") or None,
        kind=normalize_kind(document.get("kind")),
        start=optional_int(document.get("startTimeUnixNano")),
        end=optional_int(document.get("endTimeUnixNano")),
        status_code=normalize_status_code(status.get("code")),
        status_description=status.get("message"),
        attributes=otlp_attributes(document.get("attributes")),
        resource=resource,
        events=[
            {"name": event.get("name"), "time_unix_nano": optional_int(event.get("timeUnixNano")), "attributes": otlp_attributes(event.get("attributes"))}
            for event in document.get("events") or []
        ],
        links=[
            {"trace_id": link.get("traceId"), "span_id": link.get("spanId"), "attributes": otlp_attributes(link.get("attributes"))}
            for link in document.get("links") or []
        ],
    )


def span_from_console(document: dict[str, Any]) -> Span:
    context = document.get("context") or {}
    status = document.get("status") or {}
    resource = document.get("resource") or {}
    return Span(
        name=str(document.get("name", "")),
        trace_id=strip_hex_prefix(context.get("trace_id")) or "",
        span_id=strip_hex_prefix(context.get("span_id")) or "",
        parent_span_id=strip_hex_prefix(document.get("parent_id")),
        kind=normalize_kind(document.get("kind")),
        start=iso_to_nanoseconds(document.get("start_time")),
        end=iso_to_nanoseconds(document.get("end_time")),
        status_code=normalize_status_code(status.get("status_code")),
        status_description=status.get("description"),
        attributes=dict(document.get("attributes") or {}),
        resource=dict(resource.get("attributes") or {}) if isinstance(resource, dict) else {},
        events=[
            {"name": event.get("name"), "time_unix_nano": iso_to_nanoseconds(event.get("timestamp")), "attributes": dict(event.get("attributes") or {})}
            for event in document.get("events") or []
        ],
        links=[
            {
                "trace_id": strip_hex_prefix((link.get("context") or {}).get("trace_id")),
                "span_id": strip_hex_prefix((link.get("context") or {}).get("span_id")),
                "attributes": dict(link.get("attributes") or {}),
            }
            for link in document.get("links") or []
        ],
    )


def load_spans(path: str) -> tuple[list[Span], Counter[str]]:
    spans: list[Span] = []
    formats: Counter[str] = Counter()
    for document in read_documents(path):
        if not isinstance(document, dict):
            formats["ignored"] += 1
            continue
        if "resourceSpans" in document:
            formats["otlp"] += 1
            for resource_spans in document.get("resourceSpans") or []:
                resource = otlp_attributes((resource_spans.get("resource") or {}).get("attributes"))
                for scope_spans in resource_spans.get("scopeSpans") or []:
                    for span in scope_spans.get("spans") or []:
                        spans.append(span_from_otlp(span, resource))
        elif "context" in document and "trace_id" not in document:
            formats["console"] += 1
            spans.append(span_from_console(document))
        elif "trace_id" in document:
            formats["native"] += 1
            spans.append(span_from_native(document))
        else:
            formats["ignored"] += 1
    return spans, formats


# -------------------------------------------------------------------- rules


def rule_ids_well_formed(spans: list[Span]) -> Result:
    offenders: list[str] = []
    seen: Counter[str] = Counter(span.span_id for span in spans)
    for span in spans:
        if not is_hex_id(span.trace_id, 32):
            offenders.append(f"{span.label()}: trace_id {span.trace_id!r} is not 32 hex characters")
        if not is_hex_id(span.span_id, 16):
            offenders.append(f"{span.label()}: span_id {span.span_id!r} is not 16 hex characters")
        if span.parent_span_id is not None and not is_hex_id(span.parent_span_id, 16):
            offenders.append(f"{span.label()}: parent_span_id {span.parent_span_id!r} is not 16 hex characters")
    for span_id, count in seen.items():
        if count > 1:
            offenders.append(f"span_id {span_id} appears {count} times")
    return verdict("ids-well-formed", offenders, note="ids are lower case hex: 32 for a trace, 16 for a span, unique per span")


def rule_roots_are_units(spans: list[Span], vocabulary: Vocabulary | None, limit: int) -> Result:
    roots = [span for span in spans if span.parent_span_id is None]
    distinct_root_names = sorted({span.name for span in roots})
    if vocabulary is None or not vocabulary.has("spans"):
        note = "no vocabulary: only counted distinct root names; add a Root=yes row per unit of work to check them"
        if len(distinct_root_names) > limit:
            return Result("roots-are-units", WARN, len(distinct_root_names), distinct_root_names[:5], f"{len(distinct_root_names)} distinct root names exceed --max-name-cardinality {limit}; " + note)
        return Result("roots-are-units", WARN if not roots else INFO, len(distinct_root_names), distinct_root_names[:5], note)
    root_rows = vocabulary.root_spans()
    if not root_rows:
        return Result("roots-are-units", FAIL, len(roots), distinct_root_names[:5], "the vocabulary Spans table has no Root=yes row; add one per unit of work, with a glob Name such as tests/*::test_* when the root span rule builds the name")
    offenders: list[str] = []
    for span in roots:
        match = vocabulary.find_span(span.name)
        if match is None:
            offenders.append(f"root {span.label()} matches no vocabulary span")
        elif not match.root:
            offenders.append(f"root {span.label()} matches vocabulary span {match.name!r} which is Root=no")
    note = f"root span rule: {vocabulary.root_span_rule or 'not written'}; Root=yes rows: {', '.join(row.name for row in root_rows)}"
    return verdict("roots-are-units", offenders, note=note, passing_note=note)


def rule_one_parent(spans: list[Span]) -> tuple[Result, Result]:
    by_id = {span.span_id: span for span in spans}
    wrong: list[str] = []
    orphans: list[str] = []
    for span in spans:
        if span.parent_span_id is None:
            continue
        if span.parent_span_id == span.span_id:
            wrong.append(f"{span.label()} is its own parent")
            continue
        parent = by_id.get(span.parent_span_id)
        if parent is None:
            orphans.append(f"{span.label()} parent {span.parent_span_id} is not in the file")
        elif parent.trace_id != span.trace_id:
            wrong.append(f"{span.label()} parent {parent.label()} is in trace {parent.trace_id}, span is in {span.trace_id}")
    return (
        verdict("one-parent", wrong, note="a parent is a span in the same trace; a different trace is a link, not a parent"),
        verdict("orphans", orphans, failing_status=WARN, note="parents missing from the file; fine for a partial export, a bug if the export is complete"),
    )


def rule_name_cardinality(spans: list[Span], limit: int) -> Result:
    names = Counter(span.name for span in spans)
    offenders: list[str] = []
    for name in sorted(names):
        reason = looks_unbounded(name)
        if reason:
            offenders.append(f"{name!r} probably unbounded: contains {reason}; move the varying part to an attribute")
    if len(names) > limit:
        offenders.insert(0, f"{len(names)} distinct span names exceed --max-name-cardinality {limit}")
    return verdict("name-cardinality", offenders, note=f"{len(names)} distinct names in {len(spans)} spans", passing_note=f"{len(names)} distinct names in {len(spans)} spans")


def rule_names_in_vocabulary(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("spans"):
        return skipped("names-in-vocabulary", "no vocabulary Spans table")
    unknown = sorted({span.name for span in spans if vocabulary.find_span(span.name) is None})
    return verdict("names-in-vocabulary", unknown, note="a name that is not in vocabulary.md does not exist; stop and ask before adding one")


def rule_kind_matches_vocabulary(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("spans"):
        return skipped("kind-matches-vocabulary", "no vocabulary Spans table")
    offenders: list[str] = []
    for span in spans:
        row = vocabulary.find_span(span.name)
        if row is not None and row.kind and span.kind != row.kind:
            offenders.append(f"{span.label()} has kind {span.kind}, vocabulary says {row.kind}")
    return verdict("kind-matches-vocabulary", offenders)


def rule_required_attributes(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not (vocabulary.has("spans") or vocabulary.has("correlation keys")):
        return skipped("required-attributes", "no vocabulary Spans or Correlation keys table")
    offenders: list[str] = []
    every_span_keys = vocabulary.keys_on_every_span()
    for span in spans:
        missing: list[str] = []
        row = vocabulary.find_span(span.name)
        if row is not None:
            missing.extend(key for key in row.required_attributes if key not in span.attributes)
        for key, exempt in every_span_keys:
            if span.name in exempt or key in missing:
                continue
            if key not in span.attributes:
                missing.append(key)
        if missing:
            offenders.append(f"{span.label()} missing {', '.join(missing)}")
    note = "correlation keys on every span: " + ", ".join(key for key, _ in every_span_keys)
    return verdict("required-attributes", offenders, note=note, passing_note=note)


def rule_attribute_types(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    offenders: list[str] = []
    types_by_key: dict[str, set[str]] = defaultdict(set)
    for span in spans:
        for key, value in span.attributes.items():
            types_by_key[key].add(json_type(value))
            expected = vocabulary.attribute_type(key) if vocabulary else None
            if expected and json_type(value) != expected:
                offenders.append(f"{span.label()} {key}={value!r} is {json_type(value)}, vocabulary says {expected}")
    for key, types in sorted(types_by_key.items()):
        if len(types) > 1:
            offenders.append(f"{key} arrives as {' and '.join(sorted(types))}; the first document fixes the mapping")
    note = "vocabulary types checked" if vocabulary else "no vocabulary: only checked that each key keeps one JSON type"
    return verdict("attribute-types", offenders, note=note, passing_note=note)


def rule_label_values(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("span attributes"):
        return skipped("label-values", "no vocabulary Span attributes table")
    labels = vocabulary.label_keys()
    offenders: list[str] = []
    for span in spans:
        for key, allowed in labels.items():
            if key in span.attributes and str(span.attributes[key]) not in allowed:
                offenders.append(f"{span.label()} {key}={span.attributes[key]!r} not in allowed values {allowed}")
    note = "label keys: " + ", ".join(sorted(labels)) if labels else "no key of tier label lists allowed values"
    return verdict("label-values", offenders, note=note, passing_note=note)


def rule_forbidden(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    offenders: list[str] = []
    for span in spans:
        keys = list(span.attributes)
        if len(keys) > MAX_ATTRIBUTES_PER_SPAN:
            offenders.append(f"{span.label()} has {len(keys)} attribute keys, more than {MAX_ATTRIBUTES_PER_SPAN}; a growing key set is a mapping explosion")
        if vocabulary is None:
            continue
        event_keys = [key for event in span.events for key in event.get("attributes", {})]
        for key in keys + event_keys:
            entry = vocabulary.is_forbidden_key(key)
            if entry:
                offenders.append(f"{span.label()} attribute key {key!r} matches forbidden entry {entry!r}")
    note = "forbidden entries: " + ", ".join(vocabulary.forbidden) if vocabulary and vocabulary.forbidden else "no vocabulary Forbidden list: only checked the key count per span"
    return verdict("forbidden-values", offenders, note=note, passing_note=note)


def destination_keys(span: Span, vocabulary: Vocabulary | None) -> tuple[str, ...]:
    keys = DESTINATION_ATTRIBUTES
    if vocabulary is not None:
        row = vocabulary.find_span(span.name)
        if row is not None and row.destination_attribute:
            keys = (row.destination_attribute,) + keys
    return keys


def rule_exit_spans(spans: list[Span], vocabulary: Vocabulary | None) -> Result:
    offenders: list[str] = []
    for span in spans:
        keys = destination_keys(span, vocabulary)
        has_destination = any(key in span.attributes for key in keys)
        if span.kind in EXIT_KINDS and not has_destination:
            offenders.append(f"{span.label()} is {span.kind} with none of {', '.join(keys)}")
        elif span.kind not in EXIT_KINDS and has_destination:
            offenders.append(f"{span.label()} is {span.kind} but carries a destination attribute; an exit span is CLIENT or PRODUCER")
    return verdict("exit-spans-have-destination", offenders, note="without kind CLIENT or PRODUCER plus a destination the backend draws no dependency")


def exception_events(span: Span) -> list[dict[str, Any]]:
    return [event for event in span.events if event.get("name") == "exception"]


def rule_errors_are_recorded(spans: list[Span]) -> Result:
    offenders: list[str] = []
    without_description = 0
    for span in spans:
        if span.status_code != "ERROR":
            continue
        if not span.status_description:
            without_description += 1
        events = exception_events(span)
        if not events:
            offenders.append(f"{span.label()} is ERROR with no exception event; call span.record_exception(error)")
            continue
        for event in events:
            attributes = event.get("attributes", {})
            missing = [key for key in ("exception.type", "exception.message") if key not in attributes]
            if missing:
                offenders.append(f"{span.label()} exception event missing {', '.join(missing)}")
    note = f"{without_description} ERROR spans have no status description; set_status(StatusCode.ERROR, str(error))" if without_description else ""
    return verdict("errors-are-recorded", offenders, note=note, passing_note=note)


def rule_exceptions_set_status(spans: list[Span]) -> Result:
    offenders: list[str] = []
    for span in spans:
        if span.status_code == "ERROR":
            continue
        for event in exception_events(span):
            escaped = event.get("attributes", {}).get("exception.escaped")
            if escaped is False or str(escaped).lower() == "false":
                continue
            offenders.append(f"{span.label()} has an exception event but status {span.status_code}")
    return verdict("exceptions-set-status", offenders, failing_status=WARN, note="an exception that escaped the span should also set status ERROR; a handled one sets exception.escaped=false")


def rule_time_sane(spans: list[Span], tolerance_ms: float) -> tuple[Result, Result]:
    tolerance = int(tolerance_ms * 1_000_000)
    by_id = {span.span_id: span for span in spans}
    broken: list[str] = []
    outside: list[str] = []
    for span in spans:
        if span.start is None or span.end is None:
            broken.append(f"{span.label()} has no start or end time")
            continue
        if span.end < span.start:
            broken.append(f"{span.label()} ends {span.start - span.end} ns before it starts")
        parent = by_id.get(span.parent_span_id or "")
        if parent is None or parent.start is None or parent.end is None:
            continue
        if span.start < parent.start - tolerance:
            outside.append(f"{span.label()} starts {(parent.start - span.start) / 1e6:.3f} ms before parent {parent.name}")
        if span.end > parent.end + tolerance:
            outside.append(f"{span.label()} ends {(span.end - parent.end) / 1e6:.3f} ms after parent {parent.name}")
    return (
        verdict("time-sane", broken),
        verdict("children-inside-parents", outside, failing_status=WARN, note=f"tolerance {tolerance_ms} ms; an async child may legitimately outlive its parent"),
    )


def rule_links_resolve(spans: list[Span]) -> Result:
    span_ids = {span.span_id for span in spans}
    malformed: list[str] = []
    unresolved = 0
    total = 0
    for span in spans:
        for link in span.links:
            total += 1
            trace_id = strip_hex_prefix(link.get("trace_id")) or ""
            span_id = strip_hex_prefix(link.get("span_id")) or ""
            if not is_hex_id(trace_id, 32) or not is_hex_id(span_id, 16):
                malformed.append(f"{span.label()} link to trace {trace_id!r} span {span_id!r} is malformed")
            elif span_id not in span_ids:
                unresolved += 1
    if malformed:
        return verdict("links-resolve", malformed)
    if unresolved:
        return Result("links-resolve", INFO, unresolved, [], f"{unresolved} of {total} links point at spans not in this file")
    return Result("links-resolve", "PASS", 0, [], f"{total} links, all resolved in the file")


def rule_dotted_keys_note(spans: list[Span]) -> Result:
    keys = sorted({key for span in spans for key in span.attributes if "." in key and not is_known_dotted_key(key)})
    note = "Elastic APM stores span attributes that are not ECS fields under labels.* with dots replaced by underscores; record that spelling in the vocabulary's Backend spelling column. See backends/elastic/apm-server-mapping.md."
    return Result("dotted-keys-note", INFO, len(keys), keys[:5], note if keys else "no dotted keys outside known prefixes")


# --------------------------------------------------------------------- main


def run(spans: list[Span], vocabulary: Vocabulary | None, limit: int, tolerance_ms: float) -> list[Result]:
    one_parent, orphans = rule_one_parent(spans)
    time_sane, children = rule_time_sane(spans, tolerance_ms)
    return [
        rule_ids_well_formed(spans),
        rule_roots_are_units(spans, vocabulary, limit),
        one_parent,
        orphans,
        rule_name_cardinality(spans, limit),
        rule_names_in_vocabulary(spans, vocabulary),
        rule_kind_matches_vocabulary(spans, vocabulary),
        rule_required_attributes(spans, vocabulary),
        rule_attribute_types(spans, vocabulary),
        rule_label_values(spans, vocabulary),
        rule_forbidden(spans, vocabulary),
        rule_exit_spans(spans, vocabulary),
        rule_errors_are_recorded(spans),
        rule_exceptions_set_status(spans),
        time_sane,
        children,
        rule_links_resolve(spans),
        rule_dotted_keys_note(spans),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spans", required=True, help="span export: JSON Lines, OTLP/JSON, or console exporter output")
    parser.add_argument("--vocabulary", help="the project's vocabulary.md")
    parser.add_argument("--max-name-cardinality", type=int, default=200)
    parser.add_argument("--time-tolerance-ms", type=float, default=1.0)
    parser.add_argument("--json", action="store_true", help="machine readable output")
    arguments = parser.parse_args(argv)

    vocabulary = load_vocabulary(arguments.vocabulary)
    spans, formats = load_spans(arguments.spans)
    results = run(spans, vocabulary, arguments.max_name_cardinality, arguments.time_tolerance_ms)
    if vocabulary is None:
        results.insert(0, Result("vocabulary", SKIP, 0, [], "no --vocabulary: skipped roots-are-units, names-in-vocabulary, kind-matches-vocabulary, required-attributes, label-values, forbidden list, vocabulary attribute types"))
    summary = {
        "spans": len(spans),
        "traces": len({span.trace_id for span in spans}),
        "roots": sum(1 for span in spans if span.parent_span_id is None),
        "distinct_names": len({span.name for span in spans}),
        "formats": dict(formats),
        "vocabulary": vocabulary.path if vocabulary else None,
    }
    return print_report("check_spans", arguments.spans, summary, results, arguments.json)


if __name__ == "__main__":
    sys.exit(main())
