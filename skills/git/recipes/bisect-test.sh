#!/bin/sh
# A test script for `git bisect run` that runs one pytest file.
# Copy it outside the repository, edit MODULE and TEST, then:
#   git bisect run sh ../bisect-test.sh
# 0 good, 1 bad, 125 skip (cannot import, or pytest could not run the test).
MODULE=shop.money
TEST=tests/test_money.py

uv run --no-sync python -c "import $MODULE" >/dev/null 2>&1 || exit 125
uv run --no-sync python -m pytest -x -q "$TEST" >/dev/null 2>&1
case $? in
  0) exit 0 ;;    # passed
  1) exit 1 ;;    # a test failed
  *) exit 125 ;;  # 2 interrupted or collection error, 4 usage, 5 no tests
esac
