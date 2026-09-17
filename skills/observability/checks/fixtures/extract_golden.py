#!/usr/bin/env python3
"""Pull the golden data out of a worked example so the checkers can judge it.

Usage:
  python3 extract_golden.py <example.md> <outdir>

Writes into <outdir>:
  vocabulary.md  the fenced ```markdown block under the "The vocabulary" heading
  spans.jsonl    every line of the example that starts with `{`, parses as
                 JSON and carries "span_id" and "kind"
  metrics.json   the fenced block that parses as one OTLP/JSON document with
                 "resourceMetrics" (comment lines starting with // are dropped)
  logs.jsonl     every line that starts with `{`, parses as JSON and carries
                 "message" and a log level, flat ("log.level") or nested

Exit code 0 when all four were found and written, 1 otherwise, naming what
was missing. Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VOCABULARY_HEADING = re.compile(r"^#{2,3}\s+(\d+\.\s+)?the vocabulary\s*$", re.IGNORECASE)


def fenced_blocks(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """(start line index, info string, content lines) for every fenced block."""
    blocks: list[tuple[int, str, list[str]]] = []
    inside = False
    start = 0
    info = ""
    content: list[str] = []
    for index, line in enumerate(lines):
        if line.startswith("```"):
            if inside:
                blocks.append((start, info, content))
                inside = False
            else:
                inside = True
                start = index
                info = line[3:].strip()
                content = []
            continue
        if inside:
            content.append(line)
    return blocks


def vocabulary_block(lines: list[str]) -> list[str] | None:
    heading_index = None
    for index, line in enumerate(lines):
        if VOCABULARY_HEADING.match(line.strip()):
            heading_index = index
            break
    if heading_index is None:
        return None
    for start, info, content in fenced_blocks(lines):
        if start > heading_index and info.lower().startswith("markdown"):
            return content
    return None


def parse_json_line(line: str) -> dict | None:
    stripped = line.strip()
    if not stripped.startswith("{"):
        return None
    try:
        document = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return document if isinstance(document, dict) else None


def has_level(document: dict) -> bool:
    if "log.level" in document:
        return True
    log = document.get("log")
    return isinstance(log, dict) and "level" in log


def metrics_document(lines: list[str]) -> dict | None:
    for _, _, content in fenced_blocks(lines):
        text = "\n".join(line for line in content if not line.strip().startswith("//"))
        try:
            document = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(document, dict) and "resourceMetrics" in document:
            return document
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    example = Path(argv[1])
    outdir = Path(argv[2])
    lines = example.read_text(encoding="utf-8").splitlines()
    outdir.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []

    vocabulary = vocabulary_block(lines)
    if vocabulary is None:
        missing.append("vocabulary: no ```markdown block after a 'The vocabulary' heading")
    else:
        (outdir / "vocabulary.md").write_text("\n".join(vocabulary) + "\n", encoding="utf-8")

    spans: list[dict] = []
    logs: list[dict] = []
    for line in lines:
        document = parse_json_line(line)
        if document is None:
            continue
        if "span_id" in document and "kind" in document:
            spans.append(document)
        elif "message" in document and has_level(document):
            logs.append(document)
    if not spans:
        missing.append("spans: no JSON line with span_id and kind")
    else:
        (outdir / "spans.jsonl").write_text("".join(json.dumps(span) + "\n" for span in spans), encoding="utf-8")
    if not logs:
        missing.append("logs: no JSON line with message and log.level")
    else:
        (outdir / "logs.jsonl").write_text("".join(json.dumps(log) + "\n" for log in logs), encoding="utf-8")

    metrics = metrics_document(lines)
    if metrics is None:
        missing.append("metrics: no fenced block that is one OTLP/JSON document with resourceMetrics")
    else:
        (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print(f"extract_golden: {example} -> {outdir}: {len(spans)} spans, {len(logs)} log lines, {'1' if metrics else '0'} metric document, vocabulary {'found' if vocabulary else 'missing'}")
    for item in missing:
        print(f"  missing {item}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
