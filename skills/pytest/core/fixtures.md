# Fixtures

**Verdict you produce:** for a fixture name used by a test, the one
definition pytest uses, where it is, its scope, and what it depends on.

```
test:     <node id>
fixture:  <name> -> <file:line>, scope <function|class|module|package|session>
chain:    <fixtures it requests, each with file:line>
shown by: uv run pytest --fixtures-per-test <node id>
```

## Which definition is used

Ask pytest; do not work it out by reading:

```
uv run pytest --fixtures-per-test "tests/api/test_users.py::test_uses_db"
```

prints each fixture the test uses with the file and line of the
definition that won (*lab:* `db -- tests/api/conftest.py:3`, although a
root `conftest.py` also defined `db`). `uv run pytest --fixtures
tests/api` lists every fixture visible from that folder.

The rule, closest wins (*lab*, 8.4 and 9.1):

1. the test's class,
2. the test's module,
3. the `conftest.py` in the test's folder, then each parent folder's,
   up to the rootdir,
4. plugins (installed, `-p`, `pytest_plugins`), then pytest's built-ins.

An override may request the fixture it overrides, by the same name, and
receives the outer one: in `sub/conftest.py`, `def user(user): return
dict(user, role="admin")` got the root `user` and extended it (*lab*).

## Scopes and order

- Scope: `function` (default), `class`, `module`, `package`, `session`.
  A wider fixture cannot use a narrower one. *lab:* a `module` fixture
  requesting `tmp_path` failed at setup with `ScopeMismatch: You tried to
  access the function scoped fixture tmp_path with a module scoped
  request object`. Use `tmp_path_factory` for wider scopes.
- Setup follows dependencies; teardown runs in reverse (*lab:* `account`
  torn down before `user`, which it depends on).
- `--setup-show` prints each fixture's setup and teardown with its scope
  letter (`S`, `F`, ...) around each test: the evidence for questions of
  order and scope.
- Code after `yield` is the teardown; it runs even when the test fails,
  but not when the fixture's own setup failed before `yield`.

## Kinds of fixture

| Need | Write |
| --- | --- |
| a value with cleanup | `@pytest.fixture` with `yield value`, cleanup after |
| several objects per test | a factory: the fixture returns a function, and records what it made for cleanup |
| every test in a folder, without naming it | `autouse=True` in that folder's `conftest.py`; keep it rare, it hides what a test depends on |
| each test run once per backend | `@pytest.fixture(params=["sqlite", "postgres"])`, value in `request.param`; ids appear as `test_backend[sqlite]` |
| a test choosing the fixture's input | `@pytest.mark.parametrize("conn", ["a", "b"], indirect=True)`; the fixture reads `request.param` |
| a fixture for tests that do not use its value | `@pytest.mark.usefixtures("clean_db")` |
| a fixture shared by several projects | a plugin (`core/write-plugin.md`) |

## Never

- Never import from `conftest.py` in a test module (`from conftest import
  X`). *lab:* with a `conftest.py` in the test's folder and another in the
  root, `from conftest import ORDER` imported the folder's one, which did
  not define it: `ImportError: cannot import name 'ORDER' from 'conftest'`.
  Share values through fixtures, or put helpers in a normal module.
- Never change a fixture used by many tests to make one test pass;
  override it closer to that test.
- Never give a fixture a wider scope to "speed things up" when tests
  change what it returns; the change leaks between tests.
