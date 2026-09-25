# Glossary

One sentence per term. Use these words and no synonyms.

| Term | Meaning |
| --- | --- |
| test item | One test pytest will run, such as a function or one parametrized case; a `pytest.Item` node. |
| node | An element of the collection tree: `Session`, `Dir`, `Package`, `Module`, `Class`, `Function`, or a plugin's own. |
| node id | The string that names a node, such as `tests/test_x.py::TestA::test_b[1-2]`; usable on the command line. |
| collection | Finding test files and building the node tree before anything runs. |
| collector | A node that produces other nodes, such as `Module` or `Class`. |
| rootdir | The directory pytest treats as the project root; node ids and the cache are relative to it; printed in the header. |
| configfile | The one file pytest read its configuration from; printed in the header. |
| conftest.py | A file of fixtures and hooks, loaded for its directory and those below it. |
| import mode | How pytest imports test modules: `prepend` (default), `append`, or `importlib`. |
| fixture | A function marked `@pytest.fixture` that provides a value to tests that name it as a parameter. |
| fixture scope | How long a fixture value lives: `function`, `class`, `module`, `package`, `session`. |
| autouse fixture | A fixture used by every test in its visibility without being named. |
| fixture visibility | Where a fixture can be used: the class, module, or directory tree of the file that defines it, or everywhere for a plugin. |
| override | A fixture with the same name defined closer to the test, which hides the farther one. |
| finalizer | Code that runs at a fixture's teardown: the part after `yield`, or `request.addfinalizer`. |
| parametrize | Running one test or fixture once per value set, each a separate test item. |
| indirect parametrization | Sending parametrize values to a fixture as `request.param` instead of to the test. |
| marker | A label on a test, `@pytest.mark.<name>`, read by pytest or plugins; must be registered in strict mode. |
| monkeypatch | pytest's fixture for replacing attributes, dictionary items and environment variables for one test. |
| mock | An object that stands in for another and records how it was called (`unittest.mock`, `mocker`). |
| hook | A named extension point pytest calls, such as `pytest_runtest_setup`, declared by a hook specification. |
| hook specification | The declaration of a hook's name and arguments (`hookspec`), in `_pytest.hookspec` or a plugin. |
| hook implementation | A function named after a hook in a plugin or conftest (`hookimpl`). |
| firstresult hook | A hook whose call stops at the first implementation that returns something other than `None`. |
| hook wrapper | A hook implementation that runs around the others: new style `wrapper=True`, old style `hookwrapper=True`. |
| plugin | A module or object registered with pytest's plugin manager: built-in, installed (entry point `pytest11`), `-p name`, `pytest_plugins`, or a conftest. |
| pluggy | The library pytest's plugin and hook system is built on. |
| stash | A typed store on `config` and on every node (`pytest.Stash`, keys from `pytest.StashKey`) for plugins' own data; reports have none. |
| phase | One of `setup`, `call`, `teardown` for each test item; each produces a report. |
| report | A `TestReport` (per phase) or `CollectReport` (per collector) with outcome `passed`, `failed` or `skipped`. |
| outcome | What a test ended as: passed, failed, error (failed in setup or teardown), skipped, xfailed, xpassed. |
| assertion rewriting | pytest's rewriting of `assert` statements in test modules, conftests and plugins at import, to explain failures. |
| pytester | The fixture for testing pytest plugins: it writes files in a temporary directory and runs pytest on them. |
| RunResult | What `pytester.runpytest()` returns: outcomes, output lines, exit code. |
| strict mode | pytest 9's `strict` option: strict config, markers, xfail and parametrization ids together. |
