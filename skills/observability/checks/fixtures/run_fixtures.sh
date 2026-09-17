#!/bin/sh
# Runs the three checkers on the fixtures and on the golden data of the three
# worked examples, and judges the harness itself. Good fixtures must exit 0,
# bad fixtures must exit 1, every example's golden data must exit 0 against
# the example's own vocabulary. Prints PASS or FAIL per run and a final line
# for the harness. Exit code 0 when every expectation holds.
set -u
checks="$(cd "$(dirname "$0")/.." && pwd)"
cd "$checks" || exit 2
fixtures="fixtures"
examples="../examples"
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

expect 0 "check_spans.py"   --spans "$fixtures/spans.jsonl"        --vocabulary "$vocabulary"
expect 0 "check_spans.py"   --spans "$fixtures/spans_otlp.json"    --vocabulary "$vocabulary"
expect 1 "check_spans.py"   --spans "$fixtures/spans_bad.jsonl"    --vocabulary "$vocabulary"
expect 0 "check_metrics.py" --metrics "$fixtures/metrics.json"     --vocabulary "$vocabulary"
expect 0 "check_metrics.py" --metrics "$fixtures/metrics_console.json" --vocabulary "$vocabulary"
expect 1 "check_spans.py"   --spans "$fixtures/empty.jsonl"
expect 1 "check_metrics.py" --metrics "$fixtures/metrics_bad.json" --vocabulary "$vocabulary"
expect 0 "check_logs.py"    --logs "$fixtures/logs.jsonl"          --vocabulary "$vocabulary" --spans "$fixtures/spans.jsonl"
expect 1 "check_logs.py"    --logs "$fixtures/logs_bad.jsonl"      --vocabulary "$vocabulary" --spans "$fixtures/spans.jsonl"
expect 0 "check_spans.py"   --spans "$fixtures/spans.jsonl"
expect 0 "check_metrics.py" --metrics "$fixtures/metrics.json"
expect 0 "check_logs.py"    --logs "$fixtures/logs.jsonl"

# The worked examples: their golden trace, metric and logs must pass the
# checkers against their own vocabulary, or the example teaches a shape the
# checkers reject.
golden="$(mktemp -d)"
trap 'rm -rf "$golden"' EXIT
for example in test-harness web-api batch-pipeline; do
    outdir="$golden/$example"
    expect 0 "$fixtures/extract_golden.py" "$examples/$example.md" "$outdir"
    expect 0 "check_spans.py"   --spans "$outdir/spans.jsonl"     --vocabulary "$outdir/vocabulary.md"
    expect 0 "check_metrics.py" --metrics "$outdir/metrics.json"  --vocabulary "$outdir/vocabulary.md"
    expect 0 "check_logs.py"    --logs "$outdir/logs.jsonl"       --vocabulary "$outdir/vocabulary.md" --spans "$outdir/spans.jsonl"
done

if [ "$failures" -eq 0 ]; then
    echo "HARNESS PASS"
    exit 0
fi
echo "HARNESS FAIL: $failures run(s) did not exit as expected"
exit 1
