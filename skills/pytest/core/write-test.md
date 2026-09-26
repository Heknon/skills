# Write a test

**Verdict you produce:** tests that pass now and were seen to fail when
the behaviour they check was broken.

```
tests:      <node ids added or changed>
behaviour:  <one sentence per test: what must hold>
fails when: <the change to the code that made each test fail, then reverted>
run:        <summary line of the final run>
```

## Steps

1. **Name the behaviour**, in one sentence, from the requirement: "a port
   outside 1..65535 raises `ValueError`". One behaviour per test; the
   test's name says it (`test_parse_port_rejects_out_of_range`).
2. **Find the existing tests** of that code
   (`uv run pytest --co -q -k parse_port`) and follow their layout,
   fixtures and style. Put the test in the same file or folder.
3. **Arrange, act, assert.** Set up only what this behaviour needs, call
   the code once, assert on what the caller can observe: a return value,
   a raised exception, a file written, a call made at a boundary.
4. **Run it**: it must pass (or fail, if you are writing the test before
   the fix).
5. **Make it fail on purpose.** Break the behaviour in the code (return a
   wrong value, remove the check, flip a condition), run the test, see it
   fail with a message that says what broke, then undo the change and see
   it pass again. A test that still passes with the code broken tests
   nothing. Write the change you made under `fails when`. Undo the break
   in a later second, or delete the module's `__pycache__` first: *lab,
   3.12:* an undo of the same size in the same second kept the broken
   bytecode, and the test still failed.
6. Run the file, then the suite.

## Tools, all checked on pytest 9.1.1 (and 8.4.2 unless marked)

| Need | Write |
| --- | --- |
| several inputs, same behaviour | `@pytest.mark.parametrize("raw, expected", [("80", 80), ("65535", 65535)], ids=["http", "max"])` gives `test_parse_ok[http]`, `test_parse_ok[max]` |
| an exception, and its message | `with pytest.raises(ValueError, match=r"out of range: \d+"):` (`match` is a regular expression searched in `str(exc)`) |
| floats | `assert total == pytest.approx(0.3)`; `rel=`, `abs=` for tolerance |
| several checks in one test, all reported | 9.0 and later: `def test_x(subtests):` and `with subtests.test(msg="port", i=i):` around each check; failures show as `SUBFAILED[port] (i=1)`; the summary counts the test and the subtest both (*lab:* one bad subtest gave `2 failed, 2 subtests passed`: one bug, not two). On 8.4 the fixture does not exist (`fixture 'subtests' not found`): parametrize instead |
| a temporary directory | `tmp_path` (a `pathlib.Path`, new per test) |
| environment variables, attributes | `monkeypatch.setenv("KEY", "v")`, `monkeypatch.setattr(...)` (`core/mocking.md`) |
| printed output | `capsys.readouterr().out` |
| log records | `caplog.records`, `caplog.text`, `with caplog.at_level(logging.INFO):` |
| warnings | `with pytest.warns(DeprecationWarning, match="old api"):` |
| a known bug, kept visible | `@pytest.mark.xfail(reason="#123", strict=True)`: fails the run when it starts passing |

## Signs a test cannot fail

- It asserts on a value it set up itself, or on a mock's return value.
- It only asserts that a mock was called, when the behaviour is the
  result, not the call.
- It catches the exception it should let fail (`try: ... except: pass`).
- Its expected value was copied from the current output of the code.
- It has no `assert` at all, and the code cannot raise.

Step 5 catches all of these.

## Never

- Never test private helpers when the public behaviour covers them.
- Never write one test that checks ten unrelated things; when it fails,
  the name says nothing.
- Never use `time.sleep` to wait for something; wait on the condition
  with a timeout, or remove the concurrency from the test.
- Never leave a test that depends on another test having run first.
