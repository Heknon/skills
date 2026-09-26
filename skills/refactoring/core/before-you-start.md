# Before you start

**Verdict you produce:** whether the code is pinned, the baseline of
every check, and whether the change is a refactoring at all.

```
contract:  <none | stop: <name> is <serialized | stored | a route | an option | an environment variable>>
tree:      <clean | stashed "<message>" | committed <hash>>
baseline:  pytest <summary line>; ruff <line>; mypy <line>; pyright <line or "not in project">
pinned:    <tests that fail when the code is broken: <change made, then reverted> | probe .ledger/probe.py | no>
names:     .ledger/names-before.txt for <modules>
surface:   <every caller in this repository | outside callers: <entry point, README, published package, stored data>>
verdict start: <ready | pin first | stop: contract | stop: baseline red>
```

## Steps

1. **Is it a contract?** Before anything else, ask of each name the task
   renames or moves: does something outside this code read it by that
   name? Stop if it is any of these, and say which skill owns it:

   | The name is | Why it is not a refactoring | Owner |
   | --- | --- | --- |
   | a field of a request or response model, a JSON key | clients read the JSON | api, pydantic |
   | a route path, a query parameter | clients call it | api |
   | a field stored in a database | stored documents keep the old name | mongodb |
   | a command-line option, an `add_argument` name | scripts and people pass it | this repository's owners |
   | an environment variable, a settings key | deployments set it | pydantic, deployment |
   | a class whose objects are pickled or queued | stored data names its module path (`core/public-surface.md`) | the person |

   A contract can still change, on purpose, as a behaviour change with its
   own plan. It is never a step of a refactoring.
2. **Clean tree.** `git status`. Unrelated edits are committed or
   stashed first (the git skill's `core/commit.md`), so every commit of
   the refactoring holds only its step. If you keep the probe in
   `.ledger/`, add that folder to `.git/info/exclude` so it is never
   staged or stashed with a step.
3. **Baseline.** Run every check the project has, the way CI runs it
   (linting's `core/run-like-ci.md`), and write each summary line down:

   ```powershell
   uv run --no-sync pytest -q
   uv run --no-sync ruff check <the folders CI checks>
   uv run --no-sync mypy <the folders CI checks>
   uv run --no-sync python <skill>/tools/import_all.py <package> --config pyproject.toml
   ```

   A check that is already red is not yours to fix inside a refactoring.
   Stop and say so; fix it first in its own commit only if the person
   agrees. Findings that exist already are the baseline: after each step,
   only new ones count (linting's `core/in-scope.md`).
4. **Is the code pinned?** A green test suite proves nothing about code
   it does not run. For the functions you will change, break one line on
   purpose (flip a condition, return a constant), run the tests, see at
   least one fail, then restore the line (`git restore <path>`). No test
   fails: the code is not pinned. Write a probe (below) or
   characterization tests (`legacy/characterization.md`) before any step.
   In the lab, the 4 tests of a `pricing.py` passed while none of them
   covered its shared default list or the rounding of 1.275.
5. **Write the probe** that seniority's `core/scope.md` question 6
   describes, before the first edit. Two lines at its top let it import
   the project from the root folder whether or not it is installed, in a
   flat or a `src` layout:

   ```python
   import sys
   sys.path[:0] = ["", "src"]
   ```

   Call every public function you will touch, on edge inputs, and on the
   inputs the step's traps name (each `steps/` file lists them). Print
   one line per call, and catch and print exceptions, so a changed error
   shows too. Save and later compare:

   ```powershell
   uv run --no-sync python .ledger/probe.py | Out-File -Encoding utf8 .ledger/probe-before.txt
   # after each step:
   uv run --no-sync python .ledger/probe.py | Out-File -Encoding utf8 .ledger/probe-after.txt
   git diff --no-index --exit-code .ledger/probe-before.txt .ledger/probe-after.txt
   ```

   `git diff --no-index --exit-code` prints the changed lines and exits 1
   when they differ, 0 when identical (lab, PowerShell 7.5 on Linux;
   `Out-File -Encoding utf8` writes a byte order mark on Windows
   PowerShell 5.1, `not run on Windows`, which is harmless when both files
   are written the same way).
6. **Record the public names** of every module the task touches
   (`tools/public-names.md`):

   ```powershell
   uv run --no-sync python <skill>/tools/public_names.py app.reports | Out-File -Encoding utf8 .ledger/names-before.txt
   ```

7. **Who calls from outside?** Read `pyproject.toml` for
   `[project.scripts]` and `[project.entry-points]`, the README for other
   teams or services, and whether the package is built and published (a
   `[build-system]` and a version). Anything found goes in `surface`, and
   decides the shims (`core/public-surface.md`).

## Never

- Never take the first step with the baseline unknown: a check that was
  red before cannot tell you the step broke something.
- Never count tests as pins without breaking the code once.
- Never write the probe after the first edit: it would record the new
  behaviour as the old.
