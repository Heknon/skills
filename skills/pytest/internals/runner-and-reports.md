# Runner and reports

## One test's protocol (`_pytest/runner.py`, 9.1.1)

`pytest_runtest_protocol(item, nextitem)` calls `runtestprotocol`:

1. `call_and_report(item, "setup")`;
2. only if setup passed: `call_and_report(item, "call")`;
3. always: `call_and_report(item, "teardown", nextitem=...)`.

`call_and_report` does, for each phase:

```python
call = CallInfo.from_call(lambda: ihook.pytest_runtest_<phase>(item=item, ...), when=phase)
report = ihook.pytest_runtest_makereport(item=item, call=call)
ihook.pytest_runtest_logreport(report=report)
if <failure that may enter the debugger>:
    ihook.pytest_exception_interact(node=item, call=call, report=report)
```

So every test produces 2 reports (setup failed or skipped) or 3.
`SetupState` keeps the stack of set-up nodes (session, module, class,
item) so wider fixtures are torn down only when the next item leaves
their scope.

## CallInfo

`call.when` (`"setup"`, `"call"`, `"teardown"`, `"collect"`),
`call.excinfo` (an `ExceptionInfo` or `None`; `.type`, `.value`,
`.typename`), `call.duration` (seconds), `call.start`, `call.stop`,
`call.result` (raises if there was an exception).

## TestReport

| Field | |
| --- | --- |
| `nodeid`, `location` (`(path, 0-based line, name)`), `keywords` | |
| `when` | `"setup"`, `"call"`, `"teardown"` |
| `outcome` | `"passed"`, `"failed"`, `"skipped"`; also `.passed`, `.failed`, `.skipped` |
| `longrepr`, `longreprtext` | the failure representation, and as text |
| `duration`, `start`, `stop` | |
| `sections`, `capstdout`, `capstderr`, `caplog` | captured output |
| `user_properties` | `(name, value)` pairs, written to JUnit XML; add with the `record_property` fixture |
| `wasxfail` | present only on xfail/xpass reports (the reason) |

*lab*, one wrapper on `pytest_runtest_makereport` printing each report
(identical on 8.4.2 and 9.1.1):

| Test | Reports (when: outcome) |
| --- | --- |
| passing, prints `hi` | setup: passed; call: passed, `capstdout='hi\n'`; teardown: passed, `capstdout='hi\n'` (captured output accumulates) |
| failing assert | call: failed, `excinfo=AssertionError`, `longreprtext` ends `test_r.py:3: AssertionError` |
| `xfail`, fails | call: **skipped**, `wasxfail='bug 1'` |
| `xfail`, passes (xpass, not strict) | call: **passed**, `wasxfail='bug 2'` |
| `skip` mark | setup: skipped, `longrepr` a `(path, line, 'Skipped: later')` tuple; no call report |
| fixture raises | setup: failed, `excinfo=RuntimeError`; no call report; teardown: passed |

So a plugin that acts on "passed" call reports must also check
`hasattr(report, "wasxfail")`, or it will treat xpassed tests as passed
(the recipe's `test_xfail_tests_are_left_alone` failed until it did).

## How the result becomes output

`pytest_report_teststatus(report, config)` (firstresult) turns each
report into `(category, letter, word)`, such as `("failed", "F",
"FAILED")`; the terminal plugin counts categories for the summary line
and prints letters. A setup or teardown failure is categorised as
`error` ("ERROR at setup of"). Implement it to add a category of your
own.

## Changing outcomes

In a `wrapper=True` implementation of `pytest_runtest_makereport`, set
`report.outcome = "failed"` and a `report.longrepr` string; the test is
then counted as failed (the recipe's `--budget-strict`, *lab* on both
versions). Change only `when == "call"` reports: a failed setup or
teardown report is counted as an error, not a failure.
