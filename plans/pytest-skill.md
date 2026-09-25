# Plan: the pytest skill

Status: built in `skills/pytest/`. The defaults in section 6 were taken so
the skill could be built; each can be changed.

## 1. What it is

Three layers of pytest knowledge in one skill:

1. **Using pytest**: run and select tests, read a failure, decide whether
   the test or the code is wrong, write tests that can fail, fixtures,
   mocking, configuration, flaky and slow tests.
2. **Pytester**: testing pytest plugins and `conftest.py` code with the
   `pytester` fixture.
3. **Internals**: how pytest works inside (pluggy, hooks, the order they
   run in, collection and nodes, fixture resolution, assertion rewriting,
   the runner and reports, configuration and conftest loading, the stash),
   for writing plugins and for explaining behaviour that surprises.

It follows the repository's other skills: procedures that end in a
verdict, reference files with the facts, recipes that ran, evals that bait
known failures.

## 2. The environment

- A weak model, air gapped, in Zed on Windows with PowerShell; Python run
  through uv (`uv run pytest`).
- Only plugins already in the mirror; never installing one to make a test
  pass.
- Verified against pytest 9.1.1 and 8.4.2, pluggy 1.6.0, Python 3.12, with
  pytest-cov, pytest-xdist, pytest-mock, pytest-asyncio and pytest-randomly.

## 3. The failures it targets

| Failure | What it looks like |
| --- | --- |
| **Changing the check** | editing the assertion to match wrong output; `skip`, `xfail` or deleting a failing test |
| **A test that cannot fail** | asserts on a mock, or on what it just set up; passes with the code under test removed |
| **Patching the wrong name** | patches `b.f` while `a` did `from b import f` |
| **Wrong fixture** | edits a fixture in one `conftest.py` while another one is used |
| **Import trouble read as a bug** | `import file mismatch`, `ModuleNotFoundError` from rootdir, src layout or import mode |
| **Flaky, blamed on luck** | order dependence, shared state, time, randomness, xdist |
| **Plugin written from memory** | a hook that does not exist, an old-style wrapper written wrongly, attributes set on nodes instead of the stash |
| **Plugin tested by hand** | no `pytester` tests, or tests that pass without the plugin loaded |
| **Internals guessed** | "pytest calls X then Y" without evidence |

## 4. Layout

```
skills/pytest/
  SKILL.md, glossary.md
  core/         run, read a failure, test or code, write a test, fixtures,
                mocking, configuration, flaky and slow, write a plugin,
                test a plugin with pytester, debug pytest itself
  internals/    architecture (hook order recorded), hooks, pluggy,
                collection, fixtures, assertion rewriting, runner and
                reports, configuration and conftests, versions 8 and 9
  recipes/      a complete plugin package with its pytester tests, a
                pyproject configuration for 8 and for 9
  examples/     worked tasks
  evals/        scenarios and sandboxes
```

## 5. How it is verified

Every command, option, hook, error message and API in the skill was run on
pytest 9.1.1 and, where it differs, 8.4.2. The hook order in
`internals/architecture.md` was recorded with pluggy's hook call monitoring
on a real run. The plugin recipe's pytester tests pass on both versions.

## 6. Decisions taken as defaults

- **P1. Both pytest 8 and 9.** Many teams are on 8.4; the skill says where
  9 differs.
- **P2. pytest-mock where installed, `unittest.mock` otherwise.** Both are
  shown; `monkeypatch` for environment variables, attributes and paths.
- **P3. New-style hook wrappers** (`wrapper=True`) for new plugin code;
  the old `hookwrapper=True` form is documented for reading existing code.
- **P4. Plugins tested with `pytester`**, in process by default, in a
  subprocess when isolation matters.

## 7. What the lab changed

Findings that corrected a first draft or a common belief, each now in the
skill:

- pytest 8 ignores `[tool.pytest]` silently; a 9-only configuration
  makes CI on 8 fail with `ModuleNotFoundError` while the header still
  says `configfile: pyproject.toml` (`recipes/config/`, eval
  `ci-runs-pytest-8`).
- `pytest` and `python -m pytest` differ: only the second puts the
  current directory on `sys.path`.
- `from conftest import X` imports the nearest conftest, not the root one.
- `pytester.plugins` is ignored by in-process `runpytest` on 8.4 and 9.1;
  an uninstalled plugin module cannot be loaded in subprocess mode.
- Three of the plugin recipe's first tests passed with the plugin
  disabled (absence checks); the invariant "fails without the plugin"
  caught them.
- An xpassed test's call report has outcome `passed`; plugins that count
  passes must check `wasxfail` (recipe test and eval `counter-and-xpass`).
- `pytest.register_fixture` (9.1) cannot be called from a plain
  `pytest_sessionstart`; the skill registers in `pytest_collection`
  (`tryfirst=True`), the documented phase.
- A plugin's module globals are shared by the outer run and every
  in-process pytester run (a counter read 1, 2, 3), so the recipe keeps
  its state in the stash.
- Under xdist, a summary built from the stash is empty (workers have their
  own); strict failures still work. Recorded as the recipe's limitation.
- An option in a non-initial conftest is a usage error from the root
  (eval `option-in-deep-conftest`).

The independent review then found, and the lab confirmed: a conftest's
`pytest_collection_modifyitems` and summary hooks are session-wide, not
limited to its folder; `strict_markers`/`strict_config` keys exist only
from 9.0; pytest 9.0.x ignores `--strict-markers` in `addopts`; both
`[tool.pytest]` tables in one file is an error on 9; `-p no:` needs the
entry-point name, not the distribution name; `PYTEST_ADDOPTS` goes
before the command line; py.path hook arguments were removed in 9.1, not
9.0. All are fixed in the skill.

## 8. Evals

`evals/evals.json`: 11 scenarios with sandboxes, one or more per failure
in section 3. Every bait was reproduced, and every intended fix passed,
on clean pytest 9.1.1 and 8.4.2 environments.
