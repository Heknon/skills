#!/bin/sh
# Runs the ledger checker on every ledger fixture, the change checker on a
# good and a bad change, and the finish checker on a good and several bad
# finished tasks, and judges the harness itself. Good fixtures must exit 0;
# everything named bad, and the template, must exit 1. Prints PASS or
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
# a move kept importable from the old module, and a module split into a package, are not removals;
# a move that changes a default or drops a method still fails
expect 0 check_change.py --before fixtures/move/before --after fixtures/move/after_good
expect 1 check_change.py --before fixtures/move/before --after fixtures/move/after_bad
# aliases, method aliases, attribute, star and __getattr__ shims, src layouts, a function moved into an
# existing file with its except block; a changed default behind a re-export and a shim to a missing module fail
expect 0 check_change.py --before fixtures/move2/before --after fixtures/move2/after_good
expect 1 check_change.py --before fixtures/move2/before --after fixtures/move2/after_bad

expect 0 check_finish.py --dir fixtures/finish/good
expect 1 check_finish.py --dir fixtures/finish/bad_behaviour
expect 1 check_finish.py --dir fixtures/finish/bad_answer
# a probe that names its working directory by absolute path must still see the old code
cp -r fixtures/finish/bad_abs_probe "$tmp/abs_probe"
{ printf 'import sys\nsys.path.insert(0, "%s")\n' "$tmp/abs_probe"; cat fixtures/finish/good/.ledger/probe.py; } > "$tmp/abs_probe/.ledger/probe.py"
expect 1 check_finish.py --dir "$tmp/abs_probe"

if [ "$failures" -eq 0 ]; then
    echo "HARNESS PASS"
    exit 0
fi
echo "HARNESS FAIL: $failures"
exit 1
