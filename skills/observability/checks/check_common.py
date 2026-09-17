"""Shared pieces for check_spans.py, check_metrics.py and check_logs.py.

Standard library only. Holds the Result type, the vocabulary.md parser,
the vocabulary-sane rule, the JSON document reader, the OTLP attribute
normalizer, the id heuristics and the report printer. Keep this file next
to the three checkers.

The vocabulary parser keys on section names and column headers, as the
template in core/vocabulary-template.md spells them. Sections it does not
know are ignored, and so are columns it does not know, so a vocabulary may
carry more than the checkers read. What it cannot read it must say: the
vocabulary-sane rule fails a Where clause that matches no known form, a
placeholder row left in a table, a tier without its allowed values and the
other shapes that would otherwise make a rule check nothing.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Iterator

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
SKIP = "SKIP"
INFO = "INFO"

MAX_EXAMPLES = 5
VOCABULARY_TYPES = ("string", "int", "float", "bool")
VOCABULARY_TIERS = ("label", "attribute")
VOCABULARY_KINDS = ("INTERNAL", "SERVER", "CLIENT", "PRODUCER", "CONSUMER")
VOCABULARY_INSTRUMENTS = ("counter", "updowncounter", "histogram", "gauge", "none")
VOCABULARY_LEVELS = ("error", "warn", "info", "debug")
EMPTY_CELLS = ("", "none", "(none)", "-")


@dataclass
class Result:
    """One rule's outcome."""

    name: str
    status: str
    count: int = 0
    examples: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.name,
            "status": self.status,
            "count": self.count,
            "examples": self.examples[:MAX_EXAMPLES],
            "note": self.note,
        }


def verdict(
    name: str,
    offenders: list[str],
    failing_status: str = FAIL,
    note: str = "",
    passing_note: str = "",
) -> Result:
    """Build a Result from a list of offender descriptions."""
    if offenders:
        return Result(name, failing_status, len(offenders), offenders[:MAX_EXAMPLES], note)
    return Result(name, PASS, 0, [], passing_note)


def skipped(name: str, reason: str) -> Result:
    return Result(name, SKIP, 0, [], reason)


def input_not_empty(what: str, count: int) -> Result:
    """An empty export proves nothing, so it fails."""
    if count == 0:
        return Result("input-not-empty", FAIL, 0, [], f"no {what} were read from the file; an empty export is not a passing export")
    return Result("input-not-empty", PASS, count, [], f"{count} {what} read")


# ---------------------------------------------------------------- vocabulary


@dataclass
class Where:
    """A parsed Where clause of the Correlation keys table.

    The clause is exactly one of `resource`, `every span`,
    `every span except <names>`, `every log`, `every log inside a span`, or
    a span clause and a log clause joined by a comma. Names in an except
    list are separated by spaces.
    """

    resource: bool = False
    every_span: bool = False
    span_exempt: list[str] = field(default_factory=list)
    every_log: bool = False
    log_inside_span_only: bool = False


SPAN_CLAUSE = re.compile(r"^every span(?: except (\S+(?: \S+)*))?$", re.IGNORECASE)
LOG_CLAUSE = re.compile(r"^every log( inside a span)?$", re.IGNORECASE)


def parse_where(text: str) -> Where | None:
    """The Where cell as a Where, or None when it matches no known form."""
    cleaned = " ".join(clean_cell(text).split())
    if cleaned.lower() == "resource":
        return Where(resource=True)
    parts = [part.strip() for part in cleaned.split(",")]
    if not parts or len(parts) > 2:
        return None
    where = Where()
    span_match = SPAN_CLAUSE.match(parts[0])
    log_match = LOG_CLAUSE.match(parts[0])
    if span_match:
        where.every_span = True
        where.span_exempt = (span_match.group(1) or "").split()
    elif log_match and len(parts) == 1:
        where.every_log = True
        where.log_inside_span_only = bool(log_match.group(1))
        return where
    else:
        return None
    if len(parts) == 2:
        log_match = LOG_CLAUSE.match(parts[1])
        if not log_match:
            return None
        where.every_log = True
        where.log_inside_span_only = bool(log_match.group(1))
    return where


@dataclass
class VocabularySpan:
    name: str
    kind: str
    root: bool
    root_text: str
    required_attributes: list[str]
    destination_attribute: str | None


@dataclass
class VocabularyAttribute:
    key: str
    type: str
    tier: str
    allowed_values: list[str] | None  # None means unbounded


@dataclass
class VocabularyLink:
    from_span: str
    to_span: str
    relation: str


@dataclass
class VocabularyMetric:
    name: str
    instrument: str
    unit: str
    labels: list[str]
    derived: str | None  # None means the vocabulary says "no"


@dataclass
class VocabularyLog:
    template: str
    levels: list[str]
    fields: list[str]
    outside_span: bool


@dataclass
class CorrelationKey:
    key: str
    type: str
    where_text: str
    where: Where | None  # None means the clause could not be parsed


@dataclass
class Vocabulary:
    path: str
    unit: str | None = None
    root_span_rule: str | None = None
    instance_key: str | None = None
    correlation_keys: list[CorrelationKey] = field(default_factory=list)
    spans: list[VocabularySpan] = field(default_factory=list)
    attributes: dict[str, VocabularyAttribute] = field(default_factory=dict)
    events: list[dict[str, str]] = field(default_factory=list)
    links: list[VocabularyLink] = field(default_factory=list)
    metrics: dict[str, VocabularyMetric] = field(default_factory=dict)
    logs: list[VocabularyLog] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    sections: set[str] = field(default_factory=set)
    placeholders: list[str] = field(default_factory=list)  # "<section>: <cell>" rows left from the template

    # -- lookups -----------------------------------------------------------

    def has(self, section: str) -> bool:
        return section in self.sections

    def find_span(self, name: str) -> VocabularySpan | None:
        for span in self.spans:
            if span.name == name:
                return span
        for span in self.spans:
            if is_glob(span.name) and fnmatchcase(name, span.name):
                return span
        return None

    def root_spans(self) -> list[VocabularySpan]:
        return [span for span in self.spans if span.root]

    def attribute_type(self, key: str) -> str | None:
        attribute = self.attributes.get(key)
        if attribute is not None and attribute.type in VOCABULARY_TYPES:
            return attribute.type
        for correlation_key in self.correlation_keys:
            if correlation_key.key == key and correlation_key.type in VOCABULARY_TYPES:
                return correlation_key.type
        return None

    def label_keys(self) -> dict[str, list[str]]:
        """Keys of tier label that list allowed values."""
        return {
            key: attribute.allowed_values
            for key, attribute in self.attributes.items()
            if attribute.tier == "label" and attribute.allowed_values
        }

    def keys_on_every_span(self) -> list[tuple[str, list[str]]]:
        """(key, exempt span names) for correlation keys whose Where says every span."""
        return [
            (correlation_key.key, list(correlation_key.where.span_exempt))
            for correlation_key in self.correlation_keys
            if correlation_key.where is not None and correlation_key.where.every_span
        ]

    def keys_on_every_log(self) -> list[tuple[str, bool]]:
        """(key, only inside a span) for correlation keys whose Where says every log."""
        return [
            (correlation_key.key, correlation_key.where.log_inside_span_only)
            for correlation_key in self.correlation_keys
            if correlation_key.where is not None and correlation_key.where.every_log
        ]

    def is_forbidden_key(self, key: str) -> str | None:
        """The forbidden entry that matches this key, or None."""
        for entry in self.forbidden:
            if entry.endswith(".*") and key.startswith(entry[:-1]):
                return entry
            if entry.endswith("*") and key.startswith(entry[:-1]):
                return entry
            if entry == key:
                return entry
        return None


SEPARATOR_ROW = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def is_glob(text: str) -> bool:
    return "*" in text or "?" in text


def clean_cell(text: str) -> str:
    return text.strip().strip("`").strip()


def split_list(text: str) -> list[str]:
    """Comma separated cell into a clean list; none, (none), - and empty give []."""
    items = [clean_cell(item) for item in text.split(",")]
    items = [item for item in items if item]
    if len(items) == 1 and items[0].lower() in EMPTY_CELLS:
        return []
    return items


def parse_table_rows(lines: list[str], placeholders: list[str] | None = None) -> list[dict[str, str]]:
    """Every markdown table in the lines as rows keyed by lower-case header.

    Columns are matched by header, so a table may carry columns the caller
    never asks for. A row whose first cell starts with `<` is a placeholder
    left from the template; it is not a row, and it is appended to
    `placeholders` when a list is given so vocabulary-sane can name it.
    """
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
            continue
        if SEPARATOR_ROW.match(stripped):
            continue
        cells = [clean_cell(cell) for cell in stripped.strip("|").split("|")]
        if header is None:
            header = [cell.lower() for cell in cells]
            continue
        if not cells:
            continue
        if cells[0].startswith("<"):
            if placeholders is not None:
                placeholders.append(cells[0])
            continue
        row = {header[index]: cells[index] for index in range(min(len(header), len(cells)))}
        rows.append(row)
    return rows


def cell(row: dict[str, str], *names: str) -> str:
    """First matching header among names, matched by prefix."""
    for name in names:
        for header, value in row.items():
            if header.startswith(name):
                return value
    return ""


def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "preamble"
    sections[current] = []
    for line in text.splitlines():
        if line.startswith("```"):
            continue
        heading = re.match(r"^#{1,3}\s+(.*)$", line)
        if heading:
            current = heading.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return sections


def destination_key(text: str) -> str | None:
    """The Destination attribute cell as a key; `peer.service=x` gives peer.service."""
    cleaned = clean_cell(text)
    if cleaned.lower() in EMPTY_CELLS:
        return None
    return cleaned.split("=", 1)[0].strip()


def load_vocabulary(path: str | None) -> Vocabulary | None:
    if path is None:
        return None
    text = Path(path).read_text(encoding="utf-8")
    vocabulary = Vocabulary(path=path)
    sections = split_sections(text)

    def rows_of(section: str) -> list[dict[str, str]]:
        found: list[str] = []
        rows = parse_table_rows(sections[section], found)
        vocabulary.placeholders.extend(f"{section}: {placeholder}" for placeholder in found)
        return rows

    for name in ("unit of work", "preamble"):
        for line in sections.get(name, []):
            key_value = re.match(r"^\s*([a-z ]+):\s*(.+?)\s*$", line)
            if not key_value:
                continue
            key, value = key_value.group(1).strip(), clean_cell(key_value.group(2))
            if key == "unit":
                vocabulary.unit = value
            elif key == "root span name":
                vocabulary.root_span_rule = value
            elif key == "instance key":
                vocabulary.instance_key = value
    if vocabulary.unit or vocabulary.root_span_rule:
        vocabulary.sections.add("unit of work")

    if "correlation keys" in sections:
        vocabulary.sections.add("correlation keys")
        for row in rows_of("correlation keys"):
            where_text = cell(row, "where")
            vocabulary.correlation_keys.append(
                CorrelationKey(
                    key=cell(row, "key"),
                    type=cell(row, "type").lower(),
                    where_text=where_text,
                    where=parse_where(where_text),
                )
            )

    if "spans" in sections:
        vocabulary.sections.add("spans")
        for row in rows_of("spans"):
            root_text = cell(row, "root")
            vocabulary.spans.append(
                VocabularySpan(
                    name=cell(row, "name"),
                    kind=cell(row, "kind").upper(),
                    root=root_text.lower() == "yes",
                    root_text=root_text,
                    required_attributes=split_list(cell(row, "required")),
                    destination_attribute=destination_key(cell(row, "destination")),
                )
            )

    if "span attributes" in sections:
        vocabulary.sections.add("span attributes")
        for row in rows_of("span attributes"):
            allowed_text = cell(row, "allowed")
            allowed = None if allowed_text == "" or allowed_text.lower().startswith("unbounded") else split_list(allowed_text)
            key = cell(row, "key")
            vocabulary.attributes[key] = VocabularyAttribute(
                key=key,
                type=cell(row, "type").lower(),
                tier=cell(row, "tier").lower(),
                allowed_values=allowed,
            )

    if "span events" in sections:
        vocabulary.sections.add("span events")
        vocabulary.events = rows_of("span events")

    if "links" in sections:
        vocabulary.sections.add("links")
        for row in rows_of("links"):
            vocabulary.links.append(
                VocabularyLink(
                    from_span=cell(row, "from"),
                    to_span=cell(row, "to"),
                    relation=cell(row, "link.relation", "relation"),
                )
            )

    if "metrics" in sections:
        vocabulary.sections.add("metrics")
        for row in rows_of("metrics"):
            derived_text = cell(row, "derived")
            name = cell(row, "name")
            instrument = cell(row, "instrument").lower()
            derived = None if derived_text.lower() in ("", "no") else derived_text
            if instrument == "none" and derived is None:
                derived = "instrument none"
            vocabulary.metrics[name] = VocabularyMetric(
                name=name,
                instrument=instrument,
                unit=cell(row, "unit"),
                labels=split_list(cell(row, "labels")),
                derived=derived,
            )

    if "logs" in sections:
        vocabulary.sections.add("logs")
        for row in rows_of("logs"):
            vocabulary.logs.append(
                VocabularyLog(
                    template=cell(row, "message"),
                    levels=[level.lower() for level in split_list(cell(row, "level"))],
                    fields=split_list(cell(row, "fields")),
                    outside_span=cell(row, "when", "outside").lower() == "yes",
                )
            )

    if "forbidden" in sections:
        vocabulary.sections.add("forbidden")
        for line in sections["forbidden"]:
            stripped = line.strip()
            if not stripped or stripped.startswith("|"):
                continue
            stripped = re.sub(r"^[-*]\s+", "", stripped)
            for item in stripped.split(","):
                item = clean_cell(item).rstrip(".")
                # A key has no spaces; a sentence about what must never be a name is prose, not an entry.
                if item and " " not in item and not item.startswith("<"):
                    vocabulary.forbidden.append(item)

    return vocabulary


def vocabulary_problems(vocabulary: Vocabulary) -> list[str]:
    """Everything in the vocabulary that would make a rule check nothing or the wrong thing."""
    problems: list[str] = []
    for placeholder in vocabulary.placeholders:
        problems.append(f"{placeholder}: a first cell starting with < is a template placeholder, not a name; write the exact string or a glob such as tests/*::test_*")
    for correlation_key in vocabulary.correlation_keys:
        if correlation_key.where is None:
            problems.append(
                f"correlation key {correlation_key.key}: Where {correlation_key.where_text!r} matches no known clause; "
                "use resource, every span, every span except <names>, every log, every log inside a span, or a span clause and a log clause joined by a comma"
            )
        if correlation_key.type not in VOCABULARY_TYPES:
            problems.append(f"correlation key {correlation_key.key}: type {correlation_key.type!r} is not one of {', '.join(VOCABULARY_TYPES)}")
    for span in vocabulary.spans:
        if span.kind not in VOCABULARY_KINDS:
            problems.append(f"span {span.name}: kind {span.kind!r} is not one of {', '.join(VOCABULARY_KINDS)}")
        if span.root_text.lower() not in ("yes", "no"):
            problems.append(f"span {span.name}: Root {span.root_text!r} is not yes or no")
    for attribute in vocabulary.attributes.values():
        if attribute.tier == "label" and attribute.allowed_values is None:
            problems.append(f"{attribute.key} is tier label but allowed values say unbounded; a label lists its values, an unbounded key is tier attribute")
        if attribute.tier == "attribute" and attribute.allowed_values is not None:
            problems.append(f"{attribute.key} is tier attribute but lists allowed values {attribute.allowed_values}; an attribute says unbounded, a key with a list is tier label")
        if attribute.tier not in VOCABULARY_TIERS:
            problems.append(f"{attribute.key} has tier {attribute.tier!r}; use label or attribute")
        if attribute.type not in VOCABULARY_TYPES:
            problems.append(f"{attribute.key} has type {attribute.type!r}; use one of {', '.join(VOCABULARY_TYPES)}")
    for metric in vocabulary.metrics.values():
        if metric.instrument not in VOCABULARY_INSTRUMENTS:
            problems.append(f"metric {metric.name}: instrument {metric.instrument!r} is not one of {', '.join(VOCABULARY_INSTRUMENTS)}; synchronous or observable goes in a note, not the cell")
    for log in vocabulary.logs:
        if not log.levels:
            problems.append(f"log template {log.template!r}: Level is empty")
        for level in log.levels:
            if level not in VOCABULARY_LEVELS:
                problems.append(f"log template {log.template!r}: level {level!r} is not one of {', '.join(VOCABULARY_LEVELS)}; the table holds the lower case name, the shipped value is upper case")
    return problems


def rule_vocabulary_sane(vocabulary: Vocabulary | None) -> Result:
    """The vocabulary itself must be readable before it can judge anything.

    A placeholder row, a Where clause in a shape the parser does not know, a
    label without its values: each one makes a later rule check nothing and
    print PASS. Catch them here, in the file, and fail loudly.
    """
    if vocabulary is None:
        return skipped("vocabulary-sane", "no --vocabulary given")
    return verdict(
        "vocabulary-sane",
        vocabulary_problems(vocabulary),
        note="core/vocabulary-template.md holds the shapes the checkers read",
        passing_note=f"sections read: {', '.join(sorted(vocabulary.sections))}",
    )


# ---------------------------------------------------------------- json input


def iterate_json_documents(text: str) -> Iterator[Any]:
    """Yield every JSON document in the text.

    Accepts one document, JSON Lines, and pretty printed documents written
    one after another. Bad lines are skipped and reported to stderr.
    """
    decoder = json.JSONDecoder()
    position = 0
    length = len(text)
    while position < length:
        while position < length and text[position].isspace():
            position += 1
        if position >= length:
            return
        try:
            document, end = decoder.raw_decode(text, position)
        except json.JSONDecodeError as error:
            newline = text.find("\n", position)
            snippet = text[position : position + 60].replace("\n", " ")
            print(f"skipping unparsable JSON at offset {position}: {error.msg}: {snippet!r}", file=sys.stderr)
            if newline == -1:
                return
            position = newline + 1
            continue
        yield document
        position = end


def read_documents(path: str) -> list[Any]:
    return list(iterate_json_documents(Path(path).read_text(encoding="utf-8")))


# ------------------------------------------------------------- otlp helpers


def otlp_any_value(value: Any) -> Any:
    """OTLP AnyValue {stringValue: ...} into a plain JSON value."""
    if not isinstance(value, dict):
        return value
    if "stringValue" in value:
        return value["stringValue"]
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "boolValue" in value:
        return bool(value["boolValue"])
    if "bytesValue" in value:
        return value["bytesValue"]
    if "arrayValue" in value:
        return [otlp_any_value(item) for item in value["arrayValue"].get("values", [])]
    if "kvlistValue" in value:
        return otlp_attributes(value["kvlistValue"].get("values", []))
    return value


def otlp_attributes(attributes: Any) -> dict[str, Any]:
    """OTLP key value list, or an already plain dict, into a dict."""
    if isinstance(attributes, dict):
        return dict(attributes)
    result: dict[str, Any] = {}
    for item in attributes or []:
        if isinstance(item, dict) and "key" in item:
            result[item["key"]] = otlp_any_value(item.get("value"))
    return result


def optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------- type helpers


def json_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    if isinstance(value, list):
        return "array"
    return "object"


HEX_ID_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


def is_hex_id(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and bool(HEX_ID_PATTERN.match(value))


# ---------------------------------------------------------- id heuristics


UNBOUNDED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("uuid", re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")),
    ("timestamp", re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}|\d{8}T\d{6}")),
    ("hex run of 16+", re.compile(r"(?<![0-9a-zA-Z])[0-9a-fA-F]{16,}(?![0-9a-zA-Z])")),
    ("digit run of 6+", re.compile(r"\d{6,}")),
    ("[...] suffix", re.compile(r"\[[^\]]*\]\s*$")),
]


def looks_unbounded(text: str) -> str | None:
    """Why the text looks like it carries an id, or None."""
    for reason, pattern in UNBOUNDED_PATTERNS:
        if pattern.search(text):
            return reason
    return None


# ------------------------------------------------------------ dotted keys


KNOWN_DOTTED_PREFIXES = (
    "service.", "deployment.", "host.", "process.", "os.", "container.", "k8s.",
    "cloud.", "telemetry.", "otel.", "http.", "url.", "net.", "server.", "client.",
    "peer.", "db.", "messaging.", "rpc.", "exception.", "code.", "thread.", "error.",
    "event.", "log.", "trace.", "span.", "transaction.", "labels.", "user.",
    "enduser.", "faas.", "ecs.", "agent.", "file.", "source.", "destination.",
)


def is_known_dotted_key(key: str) -> bool:
    return key.startswith(KNOWN_DOTTED_PREFIXES) or key in ("@timestamp", "message")


# ------------------------------------------------------------------ report


def print_report(
    tool: str,
    input_path: str,
    summary: dict[str, Any],
    results: list[Result],
    as_json: bool,
) -> int:
    """Print the results; return the exit code."""
    exit_code = 1 if any(result.status == FAIL for result in results) else 0
    if as_json:
        print(
            json.dumps(
                {
                    "tool": tool,
                    "input": input_path,
                    "summary": summary,
                    "results": [result.to_dict() for result in results],
                    "exit_code": exit_code,
                },
                indent=2,
            )
        )
        return exit_code
    summary_text = ", ".join(f"{key}={value}" for key, value in summary.items())
    print(f"{tool}: {input_path}")
    print(f"  {summary_text}")
    for result in results:
        print(f"{result.status:<4} {result.name:<32} {result.count}")
        for example in result.examples[:MAX_EXAMPLES]:
            print(f"       - {example}")
        if result.note:
            print(f"       note: {result.note}")
    counts = {status: sum(1 for result in results if result.status == status) for status in (PASS, FAIL, WARN, SKIP, INFO)}
    counts_text = " ".join(f"{status}={count}" for status, count in counts.items() if count)
    print(f"{'OK' if exit_code == 0 else 'NOT OK'}: {counts_text}; exit {exit_code}")
    return exit_code
