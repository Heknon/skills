# Mocking

**Verdict you produce:** what is replaced, at which name, with what, and
why that boundary.

```
replaced: <module.name as the code under test looks it up>
with:     <fake value, stub function, Mock with autospec>
because:  <the boundary: network, clock, randomness, filesystem, subprocess, another service>
```

## Patch where the name is used

`app/report.py` does `from app.clock import now`. That copies the name
`now` into `app.report`. Replacing `app.clock.now` changes nothing for
`app.report`.

*lab, 9.1.1:*

| Patched | Result |
| --- | --- |
| `monkeypatch.setattr("app.clock.now", lambda: 1000)` | fails: `assert 'at 1790357860' == 'at 1000'` |
| `mocker.patch("app.clock.now", return_value=1000)` | fails the same way |
| `monkeypatch.setattr("app.report.now", lambda: 1000)` | passes |

Find the name the code under test uses: search the module for
`from X import name` or `import X` (then patch `X.name`, since the lookup
happens at call time through `X`).

## Which tool

| Tool | Use for |
| --- | --- |
| `monkeypatch` (built in) | attributes, `setenv`/`delenv`, `setitem` on dicts, `chdir`, `syspath_prepend`; undone after the test |
| `mocker` (pytest-mock, if installed) | `mocker.patch`, `mocker.spy`, `mocker.patch.object`, with `autospec=True`; undone after the test |
| `unittest.mock` directly | when pytest-mock is not installed: `with patch("app.report.now", return_value=1000):` |

- `autospec=True` makes the mock refuse calls the real function would
  refuse (wrong arguments, missing methods). Use it for anything with a
  signature.
- `mocker.spy(obj, "name")` keeps the real behaviour and records calls.

## What to mock

Mock at the boundary of the system: the network, the clock, randomness,
the filesystem outside `tmp_path`, subprocesses, other services. Do not
mock the project's own classes to test the code that uses them; then the
test checks the mock. Prefer a real small object (an in-memory store, a
`tmp_path` file) over a mock when it is cheap.

Some boundaries have their own skill:

- a FastAPI app (client, lifespan, dependency overrides): the api
  skill's `fastapi/testing.md`
- settings read from the environment: the pydantic skill's
  `settings/testing.md`
- MongoDB through mongomock, and what it cannot show: the mongodb
  skill's `pymongo/mongomock.md`

## Never

- Never assert only that a mock was called with arguments you told it to
  expect; assert on the behaviour the caller sees.
- Never patch with a string you have not confirmed exists: `monkeypatch`
  and `mocker` raise if the attribute does not exist, but a typo in a
  similar name may exist.
- Never leave a patch active across tests (a module-level `patch(...)
  .start()` without stop); use the fixtures, which undo themselves.
