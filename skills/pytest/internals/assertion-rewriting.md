# Assertion rewriting

pytest rewrites the `assert` statements of some modules at import time
(an import hook, `_pytest/assertion/rewrite.py`) so a failure shows the
values: `assert [1] == [2]` plus a diff, instead of a bare
`AssertionError`.

## Which modules are rewritten (9.1.1 source, `_should_rewrite`)

1. every `conftest.py`;
2. test files given on the command line;
3. files matching `python_files` (default `test_*.py`, `*_test.py`);
4. modules marked for rewriting, and their submodules: plugins loaded
   by `-p`, `pytest_plugins` or a `pytest11` entry point, and names
   passed to `pytest.register_assert_rewrite(...)`.

Everything else, such as a helper module `helpers/checks.py`, is
imported normally.

## What you see (*lab*, both versions)

| Situation | Failure line |
| --- | --- |
| assert in a test module | `E   assert [1] == [2]` |
| assert in a helper module | `E   AssertionError` (no values) |
| helper registered in the root conftest before any import of it: `pytest.register_assert_rewrite("helpers.checks")` | `E   assert 1 == 2` |
| registered after the module was already imported | still bare, and `PytestAssertRewriteWarning: Module already imported so cannot be rewritten; helpers.checks` |
| test module docstring contains `PYTEST_DONT_REWRITE` | `E   AssertionError` for that module |
| `--assert=plain` | bare `AssertionError` everywhere |

So: a bare `AssertionError` from a helper is not a bug in the test; it is
a module pytest did not rewrite. Register the helper package in the root
`conftest.py` (or in the plugin package's `__init__.py`) before
importing it.

## Details

- Rewritten modules are cached as
  `__pycache__/<name>.cpython-312-pytest-9.1.1.pyc`, next to the normal
  `.pyc`; the pytest version is in the name, so switching versions
  rewrites again.
- Custom failure explanations: implement
  `pytest_assertrepr_compare(config, op, left, right)` in a conftest and
  return a list of lines; `None` keeps the default.
- `-vv` shows full diffs instead of truncated ones.
- Asserting on a tuple is always true. *lab:* `assert (1 == 2, "msg")`
  passed, with `PytestAssertRewriteWarning: assertion is always true,
  perhaps remove parentheses?`.
