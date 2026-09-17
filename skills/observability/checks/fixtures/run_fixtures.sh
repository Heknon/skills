#!/bin/sh
# Runs the three checkers on the fixtures and judges the harness itself.
# Good fixtures must exit 0, bad fixtures must exit 1. Prints PASS or FAIL
# per run and a final line for the harness. Exit code 0 when every
# expectation holds.
set -u
fixtures="$(cd "$(dirname "$0")" && pwd)"
checks="$(dirname "$fixtures")"
vocabulary="$fixtures/vocabulary.md"
failures=0

expect() {
    expected="$1"
    shift
    output="$(python3 "$@" 2>&1)"
    actual=$?
    if [ "$actual" -eq "$expected" ]; then
        echo "PASS exit $actual (expected $expected): $*"
    else
        echo "FAIL exit $actual (expected $expected): $*"
        echo "$output" | sed 's/^/     /'
        failures=$((failures + 1))
    fi
}

expect 0 "$checks/check_spans.py"   --spans "$fixtures/spans.jsonl"        --vocabulary "$vocabulary"
expect 0 "$checks/check_spans.py"   --spans "$fixtures/spans_otlp.json"    --vocabulary "$vocabulary"
expect 1 "$checks/check_spans.py"   --spans "$fixtures/spans_bad.jsonl"    --vocabulary "$vocabulary"
expect 0 "$checks/check_metrics.py" --metrics "$fixtures/metrics.json"     --vocabulary "$vocabulary"
expect 0 "$checks/check_metrics.py" --metrics "$fixtures/metrics_console.json" --vocabulary "$vocabulary"
expect 1 "$checks/check_metrics.py" --metrics "$fixtures/metrics_bad.json" --vocabulary "$vocabulary"
expect 0 "$checks/check_logs.py"    --logs "$fixtures/logs.jsonl"          --vocabulary "$vocabulary" --spans "$fixtures/spans.jsonl"
expect 1 "$checks/check_logs.py"    --logs "$fixtures/logs_bad.jsonl"      --vocabulary "$vocabulary" --spans "$fixtures/spans.jsonl"
expect 0 "$checks/check_spans.py"   --spans "$fixtures/spans.jsonl"
expect 0 "$checks/check_metrics.py" --metrics "$fixtures/metrics.json"
expect 0 "$checks/check_logs.py"    --logs "$fixtures/logs.jsonl"

if [ "$failures" -eq 0 ]; then
    echo "HARNESS PASS"
    exit 0
fi
echo "HARNESS FAIL: $failures run(s) did not exit as expected"
exit 1
