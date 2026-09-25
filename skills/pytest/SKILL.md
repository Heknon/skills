---
name: pytest
description: Run, read, fix and write pytest tests, and build and test pytest plugins. Select and run tests, read a failure and decide whether the test or the code is wrong, write tests that can fail, find which fixture a name really resolves to, mock at the right place, untangle rootdir, conftest and import-mode trouble, find flaky and order-dependent tests, write conftest hooks and installable plugins, test them with the pytester fixture, and explain pytest's internals from evidence - pluggy, the hook order, collection and nodes, fixture resolution, assertion rewriting, the runner and its reports, configuration and the stash. Verified on pytest 9.1 and 8.4 with pluggy 1.6.
---

# Pytest

This skill knows how pytest behaves, from the command line down to its
hooks, and every command, option, hook and message in it was run on
pytest 9.1.1 and, where they differ, 8.4.2. Never write an option, hook,
fixture or attribute from memory: find it here, or ask pytest
(`pytest --help`, `pytest --fixtures`, `pytest --markers`, and the
installed source of `_pytest`).

Read this file, then load only what the task needs.

## Read the versions first

```
uv run pytest --version            # pytest 9.1.1
uv run python -c "import pluggy; print(pluggy.__version__)"
uv run pytest --co | Select-Object -First 10   # the header: rootdir, configfile, plugins
```

`internals/versions.md` lists what differs between 8 and 9. Run pytest
through uv (`uv run pytest`, or `uv run --no-sync pytest` to leave the
environment alone), never a bare `pytest` or `python`, which may be
another interpreter.

## The kinds of task

| Kind | You were asked to | Load |
| --- | --- | --- |
| **Run** | run some tests, a failing one, only what failed last | `core/run.md` |
| **Read** | explain a failure, an error in setup, a collection error | `core/read-failure.md` |
| **Fix** | make a failing test pass | `core/test-or-code.md`, then `core/read-failure.md` |
| **Write** | add tests for code, or improve weak tests | `core/write-test.md`, `core/fixtures.md`, `core/mocking.md` |
| **Fixture** | which fixture is used, scopes, teardown, parametrized fixtures | `core/fixtures.md` |
| **Mock** | replace a dependency, the clock, the environment, the network | `core/mocking.md` |
| **Configure** | rootdir, config files, conftest, import errors, markers, strict mode | `core/configuration.md` |
| **Flaky** | a test that fails sometimes, only in CI, only with others, or is slow | `core/flaky-and-slow.md` |
| **Plugin** | write hooks in a conftest or an installable plugin | `core/write-plugin.md`, `internals/hooks.md` |
| **Pytester** | test a plugin or conftest code | `core/pytester.md` |
| **Internals** | explain why pytest does something, or debug pytest itself | `core/debug-pytest.md`, then the `internals/` file it names |

## Where the facts are

| Folder | Holds |
| --- | --- |
| `core/` | the procedures above |
| `internals/` | architecture and the recorded hook order, hooks, pluggy, collection and nodes, fixture machinery, assertion rewriting, the runner and reports, configuration and conftests, versions |
| `recipes/` | `plugin/`, a complete installable plugin with its pytester tests, passing on 8 and 9; `config/`, pyproject settings for 8 and for 9 |
| `examples/` | three finished tasks: a failing test that was the code's fault (`fix-the-code.md`), a patch in the wrong place (`patch-where-used.md`), a plugin written and tested (`plugin-with-pytester.md`) |

`glossary.md` fixes the words.

## Invariants

1. **Never make a test pass by changing what it checks.** No editing the
   expected value to match the output, no `skip`, `xfail`, deleted
   asserts, widened `approx`, or broader `except`, unless the person
   asked for exactly that change. First decide whether the test or the
   code is wrong (`core/test-or-code.md`).
2. **A test must be able to fail.** Before trusting a new or fixed test,
   break the code it tests and watch it fail, then restore the code.
3. **Evidence from pytest, not from reading.** Which fixture is used, which
   tests are collected, which config file and rootdir are in effect, what
   a hook receives: pytest prints each (`--fixtures-per-test`, `--co`,
   the header, `--setup-show`). Run it.
4. **One failure at a time.** `-x` or a single node id, fix, rerun, then
   the whole suite.
5. **Patch where the name is used, not where it is defined.**
6. **No new plugins or packages to make tests pass.** Use what the
   environment has; air gapped, a new package cannot be installed.
7. **Plugins are tested with `pytester`**, and a plugin test must fail
   when the plugin is not loaded.
8. **Internals are claimed with evidence**: a line of `_pytest` source, a
   recorded hook order, or pytester output, never "pytest probably".

## What you say when you finish

End with these headings, each with `none` when empty. If another skill is
loaded, its headings come first and these after.

```
## Result
<what changed, or the cause found, with paths and node ids>

## Checked
<each pytest command run and its summary line, such as "12 passed in 0.8s";
for a new or fixed test, the run where it failed with the code broken>

## Not checked
<tests not run, versions or platforms not tried>
```

The `evals/` folder is for people testing this skill. Never open it while
doing a task.
