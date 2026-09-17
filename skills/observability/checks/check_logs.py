#!/usr/bin/env python3
"""Judge a log export against the invariants and the project's vocabulary.

Usage:
  python3 check_logs.py --logs logs.jsonl [--vocabulary vocabulary.md]
                        [--spans spans.jsonl] [--max-messages 200] [--json]

Input: JSON Lines, one object per line, ECS style. Dotted keys may be flat
("log.level": "info") or nested ("log": {"level": "info"}); both are read.
Expected fields per line: message, log.level, @timestamp, and trace.id plus
span.id when the line was written inside a span.

Exit code 0 when no rule is FAIL, 1 otherwise. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_common import (  # noqa: E402
    SKIP,
    WARN,
    Result,
    Vocabulary,
    input_not_empty,
    is_hex_id,
    json_type,
    load_vocabulary,
    looks_unbounded,
    print_report,
    read_documents,
    rule_vocabulary_sane,
    skipped,
    verdict,
)

ALLOWED_LEVELS = ("error", "warn", "info", "debug")
LEVEL_SPELLINGS = {"warning": "warn"}  # read as warn; the vocabulary and the shipped value spell it warn / WARN
LEVEL_ALIASES = ("log.level", "level", "levelname", "severity", "severity_text", "log_level")
TIMESTAMP_ALIASES = ("@timestamp", "timestamp", "time", "asctime", "ts")
MESSAGE_ALIASES = ("message", "msg", "event")
SECRET_KEY_PATTERN = re.compile(r"(^|[._-])(password|passwd|pwd|token|secret|authorization|api[_-]?key|access[_-]?key|private[_-]?key|cookie|set-cookie)$", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(r"^(Bearer|Basic)\s+\S+|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


@dataclass
class Line:
    number: int
    fields: dict[str, Any]

    def label(self) -> str:
        message = self.fields.get("message")
        return f"line {self.number}" + (f" {str(message)[:40]!r}" if message is not None else "")


# ------------------------------------------------------------------ loading


def flatten(document: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in document.items():
        full_key = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            flat.update(flatten(value, f"{full_key}."))
        else:
            flat[full_key] = value
    return flat


def load_lines(path: str) -> list[Line]:
    lines: list[Line] = []
    for number, document in enumerate(read_documents(path), start=1):
        if isinstance(document, dict):
            lines.append(Line(number=number, fields=flatten(document)))
    return lines


def first_present(fields: dict[str, Any], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        if alias in fields:
            return alias
    return None


def level_of(line: Line) -> str | None:
    alias = first_present(line.fields, LEVEL_ALIASES)
    if alias is None:
        return None
    level = str(line.fields[alias]).strip().lower()
    return LEVEL_SPELLINGS.get(level, level)


def template_pattern(template: str) -> re.Pattern[str]:
    parts = re.split(r"(\{[^{}]*\})", template)
    pieces = [".+?" if part.startswith("{") and part.endswith("}") else re.escape(part) for part in parts]
    return re.compile("^" + "".join(pieces) + "$", re.DOTALL)


# -------------------------------------------------------------------- rules


def rule_fields_present(lines: list[Line]) -> Result:
    offenders: list[str] = []
    renames: Counter[str] = Counter()
    for line in lines:
        missing: list[str] = []
        for canonical, aliases in (("message", MESSAGE_ALIASES), ("log.level", LEVEL_ALIASES), ("@timestamp", TIMESTAMP_ALIASES)):
            if canonical in line.fields:
                continue
            alias = first_present(line.fields, aliases)
            if alias is None:
                missing.append(canonical)
            else:
                renames[f"{alias} -> {canonical}"] += 1
        if missing:
            offenders.append(f"{line.label()} missing {', '.join(missing)}")
    note = ""
    if renames:
        note = "non ECS field names seen, rename: " + ", ".join(f"{rename} ({count} lines)" for rename, count in renames.items())
        offenders.extend(f"{count} lines use {rename.split(' -> ')[0]!r} instead of {rename.split(' -> ')[1]!r}" for rename, count in renames.items())
    return verdict("fields-present", offenders, note=note, passing_note="every line has message, log.level and @timestamp")


def rule_level_values(lines: list[Line]) -> Result:
    offenders: list[str] = []
    for line in lines:
        level = level_of(line)
        if level is not None and level not in ALLOWED_LEVELS:
            offenders.append(f"{line.label()} level {level!r} not in {list(ALLOWED_LEVELS)}")
    return verdict("level-values", offenders, note="levels are ERROR, WARN, INFO, DEBUG (warning is read as warn); see logs/levels.md")


def rule_message_templates(lines: list[Line], vocabulary: Vocabulary | None, max_messages: int) -> Result:
    messages = [str(line.fields["message"]) for line in lines if "message" in line.fields]
    distinct = Counter(messages)
    if vocabulary is not None and vocabulary.has("logs") and vocabulary.logs:
        patterns = [(row, template_pattern(row.template)) for row in vocabulary.logs]
        offenders: list[str] = []
        for line in lines:
            if "message" not in line.fields:
                continue
            message = str(line.fields["message"])
            matched = [row for row, pattern in patterns if pattern.match(message)]
            if not matched:
                offenders.append(f"{line.label()} matches no vocabulary message template")
                continue
            level = level_of(line)
            allowed_levels = {level for row in matched for level in row.levels}
            if level is not None and level not in allowed_levels:
                offenders.append(f"{line.label()} level {level!r}, vocabulary template {matched[0].template!r} says {', '.join(matched[0].levels)}")
            missing = [key for key in matched[0].fields if key not in line.fields]
            if missing:
                offenders.append(f"{line.label()} missing template fields {', '.join(missing)}")
        return verdict("message-templates", offenders, note=f"{len(patterns)} templates in the vocabulary; {{name}} placeholders match anything")
    offenders = []
    for message in sorted(distinct):
        reason = looks_unbounded(message)
        if reason:
            offenders.append(f"{message[:60]!r} probably interpolated: contains {reason}")
    if len(messages) >= 20 and len(distinct) > len(messages) / 2:
        offenders.insert(0, f"{len(distinct)} distinct messages in {len(messages)} lines: messages are probably interpolated; move values to fields")
    if len(distinct) > max_messages:
        offenders.insert(0, f"{len(distinct)} distinct messages exceed --max-messages {max_messages}")
    note = "no vocabulary Logs table: judged message cardinality by heuristics"
    return verdict("message-templates", offenders, failing_status=WARN, note=note, passing_note=note)


def rule_trace_correlation(lines: list[Line], span_trace_ids: set[str] | None) -> tuple[Result, Result]:
    broken: list[str] = []
    unknown: list[str] = []
    for line in lines:
        trace_id = line.fields.get("trace.id")
        span_id = line.fields.get("span.id")
        if trace_id is None and span_id is None:
            continue
        if trace_id is None:
            broken.append(f"{line.label()} has span.id without trace.id")
            continue
        if span_id is None:
            broken.append(f"{line.label()} has trace.id without span.id")
        if not is_hex_id(trace_id, 32):
            broken.append(f"{line.label()} trace.id {trace_id!r} is not 32 hex characters")
        if span_id is not None and not is_hex_id(span_id, 16):
            broken.append(f"{line.label()} span.id {span_id!r} is not 16 hex characters")
        if span_trace_ids is not None and trace_id not in span_trace_ids:
            unknown.append(f"{line.label()} trace.id {trace_id} is not in the span export")
    inside = sum(1 for line in lines if "trace.id" in line.fields)
    first = verdict("trace-correlation", broken, note=f"{inside} of {len(lines)} lines carry trace.id", passing_note=f"{inside} of {len(lines)} lines carry trace.id")
    if span_trace_ids is None:
        second = skipped("trace-ids-in-spans", "no --spans given")
    else:
        second = verdict("trace-ids-in-spans", unknown, failing_status=WARN, note="a trace id that no span carries may be a sampled trace or a wrong injection; open one in the backend to tell, see backends/<backend>/queries.md")
    return first, second


def rule_required_fields(lines: list[Line], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("correlation keys"):
        return skipped("required-fields", "no vocabulary Correlation keys table")
    required = vocabulary.keys_on_every_log()
    offenders: list[str] = []
    for line in lines:
        inside_span = "trace.id" in line.fields
        missing = [key for key, only_inside in required if (inside_span or not only_inside) and key not in line.fields]
        if missing:
            offenders.append(f"{line.label()} missing {', '.join(missing)}")
    note = "correlation keys on every log: " + ", ".join(key + (" (inside a span)" if only_inside else "") for key, only_inside in required)
    return verdict("required-fields", offenders, note=note, passing_note=note)


def rule_forbidden_keys(lines: list[Line], vocabulary: Vocabulary | None) -> Result:
    if vocabulary is None or not vocabulary.has("forbidden"):
        return skipped("forbidden-keys", "no vocabulary Forbidden list")
    offenders: list[str] = []
    for line in lines:
        for key in line.fields:
            entry = vocabulary.is_forbidden_key(key)
            if entry:
                offenders.append(f"{line.label()} key {key!r} matches forbidden entry {entry!r}")
    return verdict("forbidden-keys", offenders, note="forbidden entries: " + ", ".join(vocabulary.forbidden))


def rule_secrets(lines: list[Line]) -> Result:
    offenders: list[str] = []
    for line in lines:
        for key, value in line.fields.items():
            if SECRET_KEY_PATTERN.search(key):
                offenders.append(f"{line.label()} key {key!r} names a secret")
            elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
                offenders.append(f"{line.label()} key {key!r} holds a value that looks like a credential")
    return verdict("secrets", offenders, note="never log password, token, secret, authorization, api_key or their values")


def rule_field_types(lines: list[Line]) -> Result:
    types_by_key: dict[str, set[str]] = defaultdict(set)
    for line in lines:
        for key, value in line.fields.items():
            if value is not None:
                types_by_key[key].add(json_type(value))
    offenders = [f"{key} arrives as {' and '.join(sorted(types))}" for key, types in sorted(types_by_key.items()) if len(types) > 1]
    return verdict("field-types", offenders, note="a field keeps one JSON type across the file; the first document fixes the mapping")


# --------------------------------------------------------------------- main


def load_span_trace_ids(path: str | None) -> set[str] | None:
    if path is None:
        return None
    from check_spans import load_spans  # noqa: E402

    spans, _ = load_spans(path)
    return {span.trace_id for span in spans}


def run(lines: list[Line], vocabulary: Vocabulary | None, span_trace_ids: set[str] | None, max_messages: int) -> list[Result]:
    correlation, in_spans = rule_trace_correlation(lines, span_trace_ids)
    return [
        input_not_empty("log lines", len(lines)),
        rule_vocabulary_sane(vocabulary),
        rule_fields_present(lines),
        rule_level_values(lines),
        rule_message_templates(lines, vocabulary, max_messages),
        correlation,
        in_spans,
        rule_required_fields(lines, vocabulary),
        rule_forbidden_keys(lines, vocabulary),
        rule_secrets(lines),
        rule_field_types(lines),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--logs", required=True, help="JSON Lines log export")
    parser.add_argument("--vocabulary", help="the project's vocabulary.md")
    parser.add_argument("--spans", help="span export to cross check trace ids against")
    parser.add_argument("--max-messages", type=int, default=200)
    parser.add_argument("--json", action="store_true", help="machine readable output")
    arguments = parser.parse_args(argv)

    vocabulary = load_vocabulary(arguments.vocabulary)
    lines = load_lines(arguments.logs)
    span_trace_ids = load_span_trace_ids(arguments.spans)
    results = run(lines, vocabulary, span_trace_ids, arguments.max_messages)
    if vocabulary is None:
        results.insert(0, Result("vocabulary", SKIP, 0, [], "no --vocabulary: skipped vocabulary-sane, message templates, required-fields, forbidden-keys"))
    summary = {
        "lines": len(lines),
        "distinct_messages": len({str(line.fields.get("message")) for line in lines}),
        "levels": dict(Counter(level_of(line) or "missing" for line in lines)),
        "vocabulary": vocabulary.path if vocabulary else None,
        "spans": arguments.spans,
    }
    return print_report("check_logs", arguments.logs, summary, results, arguments.json)


if __name__ == "__main__":
    sys.exit(main())
