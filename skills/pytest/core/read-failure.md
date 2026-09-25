# Read a failure

**Verdict you produce:** what failed, in which phase, and the one line
that says why.

```
test:   <node id>
phase:  <collection | setup | call | teardown>
error:  <the E line>
where:  <file:line of the > marker, and whose code it is: test, fixture, code under test, pytest>
```

## The kinds of output

All shapes below are from the lab (pytest 9.1.1, `-rA`).

| Seen | Phase | Meaning |
| --- | --- | --- |
| `ERROR collecting test_x.py` and `Interrupted: 1 error during collection` | collection | the test module could not be imported or collected; **no test ran at all**. Often `ModuleNotFoundError`, a syntax error, or configuration (`core/configuration.md`). `--continue-on-collection-errors` runs the rest |
| `ERROR at setup of test_x` | setup | a fixture failed before the test; the test body never ran |
| `fixture 'nope' not found` with `available fixtures: ...` | setup | a parameter names no fixture visible here: a typo, a missing plugin, or a fixture defined in a conftest that does not cover this directory |
| `FAILED ... AssertionError` with `>` on an `assert` | call | the test ran and an assertion failed; the `E` lines explain the values |
| `Failed: DID NOT RAISE ValueError` (8.4: `DID NOT RAISE <class 'ValueError'>`) | call | `pytest.raises` expected an exception and the code returned normally |
| `FAILED ... <SomeError>` with `>` in the code under test | call | the code raised; read up the traceback to the first frame in the project |
| `ERROR at teardown of test_x` | teardown | cleanup failed after the test; the test itself is counted as passed **and** as an error (*lab:* `PASSED test_teardown_error` and `ERROR test_teardown_error`) |
| `XFAIL ... - reason` | call | expected to fail, and failed: not a problem |
| `XPASS ... - reason` | call | expected to fail, but passed: the bug may be fixed; with `xfail_strict = true` (or `strict=True` on the marker) it fails the run as `[XPASS(strict)]` |
| `SKIPPED [1] file:line: reason` | setup (a `skip`/`skipif` marker) or call (`pytest.skip()` in the test body) | skipped |
| `async def functions are not natively supported` and `FAILED` | call | an `async def` test without an async plugin; *lab:* failed on 8.4.2 and 9.1.1. Use the async plugin the project already has (pytest-asyncio: `@pytest.mark.asyncio`, or its `asyncio_mode`); never install one to make it pass |
| warnings summary | any | a warning was raised; not a failure unless `-W error` or `filterwarnings = error` is set |

The progress line uses the same letters: `E.EFxXs.E` was error, pass,
error, fail, xfail, xpass, skip, pass, error.

## Reading an assertion

```
>       assert data == {"a": 1, "b": [1, 3]}
E       AssertionError: assert {'a': 1, 'b': [1, 2]} == {'a': 1, 'b': [1, 3]}
E         Omitting 1 identical items, use -vv to show
E         Differing items:
E         {'b': [1, 2]} != {'b': [1, 3]}
```

- The left side is what the code produced, the right side what the test
  expects, when the test is written `assert actual == expected`.
- `-vv` shows the full values and diff.
- A bare `AssertionError` with no values means the `assert` was in a
  module pytest did not rewrite, such as a helper imported by the test
  (*lab*; `internals/assertion-rewriting.md`).

## Steps

1. Run the one failing test alone, with `-vv` and `--tb=long` if the
   default is not enough (`core/run.md`).
2. Name the phase from the header line (`ERROR at setup of`, `FAILED`,
   `ERROR at teardown of`, `ERROR collecting`).
3. Find the `>` line and the `E` lines. Whose file is it: the test, a
   fixture, the project's code, a third-party package, `_pytest`?
4. For an exception, read the traceback from the bottom up to the first
   frame in the project's own code; that is where the cause usually is.
5. Then decide what is wrong: `core/test-or-code.md`.

## Never

- Never explain a collection error as a test failure: nothing ran.
- Never read only the last line; the `>` line and its file decide whose
  fault it is.
