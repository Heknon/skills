passed_calls = 0


def pytest_runtest_logreport(report):
    global passed_calls
    if report.when == "call" and report.passed:
        passed_calls += 1


def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_line(f"team dashboard: {passed_calls} passed")
