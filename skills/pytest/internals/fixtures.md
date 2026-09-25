# Fixtures inside

For using fixtures, see `core/fixtures.md`. This file is for plugins and
for questions about how pytest resolves them.

## Objects

| Object | What it is |
| --- | --- |
| `FixtureManager` | `session._fixturemanager`; finds and registers fixture definitions |
| `FixtureDef` | one definition: `argname`, `func`, `scope`, `params`, `ids`, `cached_result`, finalizers |
| `FixtureRequest` (`request`) | the requesting context: `request.node`, `request.scope`, `request.param`, `request.config`, `request.getfixturevalue(name)`, `request.addfinalizer(fn)`, `request.fixturename` |
| `item.fixturenames` | the closure: every fixture the test needs, directly or through other fixtures, plus autouse ones |

## When things happen

- **Collection:** when a module, class, conftest or plugin is collected
  or registered, its `@pytest.fixture` functions become `FixtureDef`s
  visible from that node down. For each test function, pytest computes
  the closure and `pytest_generate_tests` turns fixture `params` into
  test cases.
- **Setup** (`pytest_runtest_setup`): each fixture in the closure is
  created through `pytest_fixture_setup(fixturedef, request)`, wider
  scopes first; the value is cached on the `FixtureDef` for its scope.
- **Teardown:** finalizers run in reverse; then
  `pytest_fixture_post_finalizer`. A wider-scoped fixture is torn down
  when the next test no longer shares its scope (`SetupState` in
  `_pytest/runner.py`).

## Which definition wins

Closest to the test in the collection tree wins: class, module, the
nearest conftest, parent conftests, then plugins (*lab*, both versions;
evidence with `--fixtures-per-test`). pytest 9.1 formalised this as
**visibility**: a definition registered for a more specific node beats
one for a more general node, whatever the registration order; equal or
unrelated visibility keeps "last registered wins" (9.1 changelog,
#14513). This only changes behaviour for plugins that register several
fixtures of the same name programmatically.

## Registering a fixture from code (9.1 and later)

```python
@pytest.hookimpl(trylast=True)       # after pytest's own sessionstart creates the fixture manager
def pytest_sessionstart(session):
    pytest.register_fixture(name="db", func=_make_db, node=session, scope="session")
```

- `node` sets visibility: `session` for everywhere, a `Dir` or `Module`
  node for that part of the tree.
- *lab:* without `trylast=True`, `AttributeError: 'Session' object has
  no attribute '_fixturemanager'`. With it, `--fixtures-per-test`
  showed `db -- plug.py:3`, and a `db` fixture in `sub/conftest.py` still
  won for tests in `sub/`.
- *lab, 8.4:* `module 'pytest' has no attribute 'register_fixture'`. On
  8.x define the fixture with `@pytest.fixture` in the plugin module.

## Deprecated in 9.1 (removal in 10)

- `FixtureDef(baseid=...)` and `nodeid=` strings to
  `parsefactories`/`_register_fixture`: pass `node=` instead
  (`node=session` for global).
- `FixtureDef.has_location`.
- `request.getfixturevalue()` during teardown for a fixture not already
  requested.
- Class-scoped fixtures defined as instance methods.
