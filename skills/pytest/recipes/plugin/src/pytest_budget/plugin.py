"""pytest-budget: report tests whose call phase is slower than a budget.

Shows each part of a plugin: an option with an ini fallback, a marker,
a fixture, a new-style hook wrapper, the stash, and a terminal summary.
"""

from __future__ import annotations

import pytest

# Data the plugin keeps on the config object. A StashKey is typed and
# private to this plugin; no attribute is added to pytest's objects.
over_budget_key = pytest.StashKey[list[tuple[str, float, float]]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("budget", "time budget per test")
    group.addoption(
        "--budget-ms",
        type=float,
        default=None,
        help="report tests whose call takes longer than this (milliseconds)",
    )
    group.addoption(
        "--budget-strict",
        action="store_true",
        default=False,
        help="fail tests that are over budget",
    )
    # Configuration-file fallback for --budget-ms.
    parser.addini("budget_ms", help="default for --budget-ms", default="")


def pytest_configure(config: pytest.Config) -> None:
    # Register the marker so --strict-markers accepts it and --markers lists it.
    config.addinivalue_line(
        "markers", "budget(ms): time budget for this test, in milliseconds"
    )
    config.stash[over_budget_key] = []


def _default_budget(config: pytest.Config) -> float | None:
    value = config.getoption("budget_ms")
    if value is not None:
        return value
    ini = config.getini("budget_ms")
    return float(ini) if ini else None


def _budget_for(item: pytest.Item) -> float | None:
    marker = item.get_closest_marker("budget")
    if marker is not None:
        return float(marker.args[0])
    return _default_budget(item.config)


@pytest.fixture
def budget(request: pytest.FixtureRequest) -> float | None:
    """The time budget, in milliseconds, that applies to this test."""
    return _budget_for(request.node)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    # Everything before the yield runs before the other implementations;
    # the yield returns the report they built.
    report = yield
    # Only passed calls. xfail tests are left alone: an xpassed test has
    # outcome "passed" and a wasxfail attribute.
    if report.when != "call" or not report.passed or hasattr(report, "wasxfail"):
        return report
    limit = _budget_for(item)
    took_ms = call.duration * 1000
    if limit is None or took_ms <= limit:
        return report
    item.config.stash[over_budget_key].append((item.nodeid, took_ms, limit))
    if item.config.getoption("budget_strict"):
        report.outcome = "failed"
        report.longrepr = f"over budget: took {took_ms:.0f} ms, budget {limit:.0f} ms"
    return report


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, config: pytest.Config
) -> None:
    over = config.stash.get(over_budget_key, [])
    if not over:
        return
    terminalreporter.section("over budget")
    for nodeid, took_ms, limit in over:
        terminalreporter.write_line(f"{nodeid}: {took_ms:.0f} ms (budget {limit:.0f} ms)")
