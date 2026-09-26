# Run and select tests

**Verdict you produce:** the command that runs exactly the tests asked
for, and its summary line.

```
command: uv run pytest <selection> <options>
result:  <summary line, such as "1 failed, 12 passed in 0.84s">, exit code <n>
```

## Selecting

| Select | Write (PowerShell and POSIX alike) |
| --- | --- |
| a folder or file | `uv run pytest tests/api` / `uv run pytest tests/api/test_users.py` |
| one test | `uv run pytest tests/api/test_users.py::test_login` |
| a test in a class | `uv run pytest "tests/api/test_users.py::TestLogin::test_ok"` |
| one parametrized case | `uv run pytest "tests/test_x.py::test_pair[1-2]"` |
| by name expression | `uv run pytest -k "login and not slow"` |
| by marker | `uv run pytest -m "not integration"` |
| what failed last time | `uv run pytest --lf`; failed first, then the rest: `--ff` |
| from the first failure onward, one at a time | `uv run pytest --sw` (stepwise) |
| tests from new files first, then the rest | `uv run pytest --nf` |

- Copy node ids from pytest's own output (`--co -q`, the `FAILED` lines).
  Quote them: in the lab, PowerShell passed `test_x.py::test_pair[1-2]`
  unquoted, but an id with a space (`test_pair[x y-z]`) needs quotes.
- `-k` matches substrings of node names, class names, markers and
  keywords, case-insensitively, with `and`, `or`, `not` and parentheses.
- `--lf` with nothing recorded as failed runs everything (*lab:* `4
  passed`); the record lives in `.pytest_cache`.
- List without running: `uv run pytest --co -q` prints node ids;
  `--co` alone prints the tree with modules and classes.

## Options worth knowing

| Option | Does |
| --- | --- |
| `-x`, `--maxfail=3` | stop after the first, or third, failure |
| `-v`, `-vv` | one line per test; `-vv` shows full diffs |
| `-q` | shorter output |
| `-rA` | summary of all outcomes at the end; letters `f` failed, `E` error, `s` skipped, `x` xfailed, `X` xpassed, `p` passed, `P` passed with output, `a` all but passed |
| `--tb=short\|long\|line\|native\|no` | traceback style |
| `-l`, `--showlocals` | local variables in tracebacks |
| `-s` | do not capture output (see `print` live) |
| `--pdb`, `--trace` | debugger on failure; at the start of each test (interactive: not for an agent) |
| `--durations=10` | the ten slowest phases |
| `-p no:randomly` | turn off a plugin for this run, by its name from the header |
| `-o key=value` | override a configuration value |
| `-n 4`, `-n auto` | parallel workers, if pytest-xdist is installed |
| `--no-header`, `--no-summary` | shorter output for pasting |

`--pdb` and a `breakpoint()` in the code wait forever when stdin is open
and silent, as in an agent's terminal (*lab, 9.1.1:* both ran until an
8 s time limit stopped them). The forms that end are the debugging
skill's `tools/pdb.md`.

## Exit codes

| Code | Meaning (*lab*) |
| --- | --- |
| 0 | all selected tests passed |
| 1 | some tests failed |
| 2 | interrupted: by the user, or collection errors stopped the run |
| 3 | internal error |
| 4 | usage error, such as an unknown option (`--no-such-option` gave 4) |
| 5 | no tests collected (`-k nomatch` gave 5) |

In PowerShell the code is in `$LASTEXITCODE` after the command.

## Never

- Never run the whole suite over and over while fixing one test; select
  it, fix it, then run the whole suite once.
- Never add `-p no:<plugin>` or `-o` overrides to configuration files to
  make a run pass; use them on the command line to investigate.
