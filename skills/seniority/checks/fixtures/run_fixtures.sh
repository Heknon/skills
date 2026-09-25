#!/bin/sh
# Runs the ledger checker on every fixture and on the ledger of every worked
# example, the change checker on a good and a bad change, and the finish
# checker on a good and two bad finished tasks and on every example's
# ledger and answer, and judges the harness itself. Good fixtures and
# every example must exit 0; everything named bad, and the template, must
# exit 1. The finish check on an example also proves its answer quotes the
# ledger check's real summary. Prints PASS or
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

expect 0 check_finish.py --dir fixtures/finish/good
expect 1 check_finish.py --dir fixtures/finish/bad_behaviour
expect 1 check_finish.py --dir fixtures/finish/bad_answer

for example in ../examples/*.md; do
    name="$(basename "$example" .md)"
    expect 0 fixtures/extract_golden.py "$example" "$tmp/$name"
    expect 0 check_ledger.py --ledger "$tmp/$name/ledger.md"
    expect 0 check_finish.py --dir "$tmp/$name" --ledger "$tmp/$name/ledger.md" --answer "$tmp/$name/answer.md" --no-change-check
done

if [ "$failures" -eq 0 ]; then
    echo "HARNESS PASS"
    exit 0
fi
echo "HARNESS FAIL: $failures"
exit 1
