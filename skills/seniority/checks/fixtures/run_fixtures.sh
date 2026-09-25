#!/bin/sh
# Runs the ledger checker on every fixture and on the ledger of every worked
# example, and the change checker on a good and a bad change, and judges
# the harness itself. Good fixtures and every example
# must exit 0; each *_bad.md and template.md must exit 1; each example's
# answer must quote the summary line the checker really prints. Prints PASS or
# FAIL per run and a final line for the harness. Exit code 0 when every
# expectation holds.
set -u
checks="$(cd "$(dirname "$0")/.." && pwd)"
cd "$checks" || exit 2
failures=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

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

for good in fixtures/good.md fixtures/in_progress.md fixtures/risky_good.md; do
    expect 0 check_ledger.py --ledger "$good"
done
for bad in fixtures/*_bad.md fixtures/template.md; do
    expect 1 check_ledger.py --ledger "$bad"
done
expect 0 check_change.py --before fixtures/change/before --after fixtures/change/after_good
expect 1 check_change.py --before fixtures/change/before --after fixtures/change/after_bad
expect 1 check_change.py --before fixtures/change/missing --after fixtures/change/after_good

for example in ../examples/*.md; do
    name="$(basename "$example" .md)"
    expect 0 fixtures/extract_golden.py "$example" "$tmp/$name"
    expect 0 check_ledger.py --ledger "$tmp/$name/ledger.md"
    actual="$(python3 check_ledger.py --ledger "$tmp/$name/ledger.md" | tail -1)"
    quoted="$(cat "$tmp/$name/expected_summary.txt" 2>/dev/null)"
    if [ "$actual" = "$quoted" ]; then
        echo "PASS $name quotes the checker's real summary: $actual"
    else
        echo "FAIL $name quotes '$quoted' but the checker prints '$actual'"
        failures=$((failures + 1))
    fi
done

if [ "$failures" -eq 0 ]; then
    echo "HARNESS PASS"
    exit 0
fi
echo "HARNESS FAIL: $failures"
exit 1
