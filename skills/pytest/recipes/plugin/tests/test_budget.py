"""pytester tests for pytest-budget.

Each test writes a small test file into a temporary directory
(pytester.path), runs pytest on it, and checks the output. The plugin is
loaded in the inner run through its installed entry point, the way users
get it; test_plugin_is_registered fails if the entry point is missing.

A check that something is absent (no_fnmatch_line) also passes when the
plugin is not loaded at all, so every such test also asserts something
only the loaded plugin can produce.
"""

import pytest

SLOW = """
    import time
    def test_slow():
        time.sleep(0.2)
"""


def test_plugin_is_registered(pytester: pytest.Pytester) -> None:
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(["*--budget-ms=BUDGET_MS*"])
    result.stdout.fnmatch_lines(["*budget_ms*default for --budget-ms*"])


def test_marker_is_registered(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        @pytest.mark.budget(1000)
        def test_fast():
            pass
        """
    )
    result = pytester.runpytest("--strict-markers")
    result.assert_outcomes(passed=1)


def test_reports_slow_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(SLOW)
    result = pytester.runpytest("--budget-ms=50")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        ["*= over budget =*", "test_reports_slow_test.py::test_slow: * ms (budget 50 ms)"]
    )


def test_silent_within_budget(pytester: pytest.Pytester) -> None:
    # --budget-ms is a usage error without the plugin, so passed=1 proves
    # the plugin was loaded.
    pytester.makepyfile(SLOW)
    result = pytester.runpytest("--budget-ms=5000")
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*over budget*")


def test_no_budget_no_report(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import time
        def test_slow(budget):
            assert budget is None
            time.sleep(0.2)
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*over budget*")


def test_strict_fails_slow_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(SLOW)
    result = pytester.runpytest("--budget-ms=50", "--budget-strict")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*over budget: took * ms, budget 50 ms*"])
    assert result.ret == pytest.ExitCode.TESTS_FAILED


def test_budget_from_ini(pytester: pytest.Pytester) -> None:
    pytester.makeini(
        """
        [pytest]
        budget_ms = 50
        """
    )
    pytester.makepyfile(SLOW)
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*test_slow: * ms (budget 50 ms)"])


def test_option_beats_ini(pytester: pytest.Pytester) -> None:
    pytester.makeini(
        """
        [pytest]
        budget_ms = 50
        """
    )
    pytester.makepyfile(SLOW)
    result = pytester.runpytest("--budget-ms=5000")
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*over budget*")


def test_marker_beats_option(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import time, pytest
        @pytest.mark.budget(5000)
        def test_slow_but_allowed():
            time.sleep(0.2)
        """
    )
    result = pytester.runpytest("--budget-ms=50")
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*over budget*")


def test_fixture_gives_budget(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        def test_default(budget):
            assert budget == 50
        @pytest.mark.budget(7)
        def test_marked(budget):
            assert budget == 7
        """
    )
    result = pytester.runpytest("--budget-ms=50")
    result.assert_outcomes(passed=2)


def test_failing_test_is_not_reported(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import time
        def test_slow_and_broken():
            time.sleep(0.2)
            assert False
        """
    )
    result = pytester.runpytest("--budget-ms=50", "--budget-strict")
    result.assert_outcomes(failed=1)
    result.stdout.no_fnmatch_line("*over budget*")


def test_xfail_tests_are_left_alone(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import time, pytest
        @pytest.mark.xfail(reason="known bug")
        def test_xpass():
            time.sleep(0.2)
        def test_slow(budget):
            time.sleep(0.2)
        """
    )
    result = pytester.runpytest("--budget-ms=50", "--budget-strict")
    result.assert_outcomes(xpassed=1, failed=1)
    result.stdout.no_fnmatch_line("*test_xpass: *")
