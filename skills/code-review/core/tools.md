# Tools: run what the project runs, report what is new

**Verdict you produce:** each tool and the tests, run on the change and
on its base, with their summary lines and the new errors only.

```
ci runs:   ruff check ., mypy, pytest  (.gitlab-ci.yml jobs lint, test)
head:      ruff: Found 2 errors. | mypy: Success: no issues found in 7 source files | pytest: 3 passed
base:      ruff: All checks passed!
new:       src/library/reviews.py:10:41: B006 Do not use mutable data structures for argument defaults
           tests/test_api.py:9:89: E501 Line too long (91 > 88)
verdict tools: <clean | new errors: N (CI fails) | tests fail: <node ids> | could not run: <what, why>>
```

Tools are evidence, not the review. They report what their rules
cover; the review adds what they cannot see. Their lines go under
*Checked* once, with the command; they are never retold as findings
(invariant 5).

## Steps

1. **Find what CI runs**: linting `core/run-like-ci.md`, step 1 (the CI
   file and its includes, the exact commands). No CI file: run what
   `pyproject.toml` configures (`[tool.ruff]`, `[tool.mypy]`,
   `[tool.pyright]`, `[tool.pytest.ini_options]`), and say that CI was
   not seen. Check the versions against the lock as linting's
   invariant 1 says; a global tool's verdict does not count.
2. **Run them on the change**, the way CI runs them, and keep each
   output in a file outside the repository:

   ```powershell
   uv run --no-sync ruff check --output-format concise . > $env:TEMP\head-ruff.txt
   uv run --no-sync mypy > $env:TEMP\head-mypy.txt
   uv run --no-sync pytest -q -p no:cacheprovider
   ```

   `--output-format concise` prints one line per finding
   (`path:line:col: CODE message`); the default `full` format prints a
   code frame per finding (*lab*, ruff 0.16.9). `-p no:cacheprovider`
   keeps pytest from writing `.pytest_cache`. Windows PowerShell 5.1
   writes these files as UTF-16 (*not run on Windows*);
   `review_diff.py newerrors` reads both.
3. **Run them on the base** only when the change has findings from a
   tool, to tell new ones from old ones:

   ```powershell
   git switch --detach (git merge-base origin/main HEAD)   # or run merge-base first and paste the hash
   uv run --no-sync ruff check --output-format concise . > $env:TEMP\base-ruff.txt
   uv run --no-sync mypy > $env:TEMP\base-mypy.txt
   git switch -                                            # back to the branch
   git branch --show-current                               # prints the branch name again
   uv run --no-sync python <skill>\recipes\review_diff.py newerrors $env:TEMP\base-ruff.txt $env:TEMP\head-ruff.txt
   ```

   The same `.venv` serves both commits (*lab*: `git switch --detach`
   and `git switch -` kept `.venv`, and `git branch --show-current`
   printed nothing while detached). `newerrors` compares without line
   numbers, so a finding that only moved is not new (*lab*: `2 new tool
   line(s)`, B006 and E501, on a change whose base was clean). A
   command inside a git argument in PowerShell: git's
   `reference/windows.md` (*not run on Windows*).
4. **Read each new tool line** with linting (`core/read-finding.md`,
   `ruff rule <CODE>`), only to know what it means. Then it goes under
   *Checked* as it is.
5. **A line a tool flagged becomes a finding only with a scenario the
   tool did not state.** ruff `S110` or `BLE001` on `except Exception:
   pass` is a tool line; "the store is down and the client is told the
   write was saved" is the finding, citing the tool line.
6. **Tests.** Failing tests on the change that pass on the base are a
   finding (blocker: CI is red). Note tests that were skipped or could
   not run (a database not reachable), and what that leaves unverified.

## Run a case

A finding is strongest when you ran the input (evidence `ran`). Cheap,
side-effect-free calls run in the project's interpreter:

```powershell
uv run --no-sync python -c "from library.loans import loan_slip; print(loan_slip('b-9', 'Ann'))"
```

For a blocker or major that needs more than one line, write a
throwaway reproduction outside the repository (CR5): debugging's
`recipes/repro_template.py`, copied to `$env:TEMP`, answers with exit
1 when the bug shows (*lab*: `BAD (1): ... raised AttributeError(...)`
on the branch, `GOOD (0)` on main). A pytest file outside the
repository runs with `rootdir` set to its own folder and no config
file; add `-c pyproject.toml --rootdir=.` from the project root to get
the project's settings (*lab*, pytest 9.1.1). Delete the folder after,
and say in *Checked* what ran and that it was removed.

## Never

- Never install a tool, stub or plugin to review (linting invariant 9).
- Never run `ruff check --fix` or `ruff format` on the change: the
  review does not edit code (CR4).
- Never `approve` when nothing ran (invariant 3). When the tools cannot
  run, say why under *Checked*; the verdict is at best `cannot judge`
  for a change whose correctness needs them.
