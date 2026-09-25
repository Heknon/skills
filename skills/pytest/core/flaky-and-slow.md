# Flaky and slow tests

**Verdict you produce:** why a test passes sometimes and fails
sometimes, shown by a command that makes it fail every time.

```
test:       <node id>
fails with: <command that fails it every time: seed, order, worker, environment>
passes with:<command that passes it>
cause:      <shared state | order | time | randomness | network | parallel workers | resource>
fix:        <what changed in the test or code; never a retry>
```

"Flaky" is not a cause. A test that fails sometimes has a reason; find
the command that makes it fail every time, and the reason follows.

## Steps

1. **Run it alone**: `uv run pytest -p no:randomly "<node id>"`. If it
   fails alone but passes in the suite, it depends on something another
   test did. *lab:* `test_reads` read a module-level dict that
   `test_writes` filled: `3 passed` in file order, `1 failed` alone.
2. **Run it in another order.** If pytest-randomly is installed (its name
   is on the `plugins:` line of the header), it shuffles every run and
   prints the seed in the header: `Using --randomly-seed=1`. Rerun with
   that seed to repeat the order exactly: `uv run pytest
   --randomly-seed=1` (*lab:* failed the same way both times). Rerun the
   last seed with `--randomly-seed=last`. Turn the shuffle off with `-p
   no:randomly` (accepted, and ignored, when the plugin is not installed).
3. **Run it under xdist** if the suite uses `-n`: workers split tests, so
   tests that relied on order break. *lab:* with `-n 2`, `test_writes`
   ran on `gw0`, `test_reads` on `gw1`, and failed. The `[gw1]` prefix
   on each `-v` line says which worker ran what.
4. **Look for the other causes** when order is not it:

| Cause | Sign | Fix |
| --- | --- | --- |
| shared state | module globals, class attributes, caches, singletons, environment variables, the working directory | reset it in a fixture (`monkeypatch.setattr(module, "CACHE", {})`, `monkeypatch.setenv`, `monkeypatch.chdir`), or remove the global |
| time | `datetime.now()`, `time.time()`, midnight, time zones, `sleep` | pass the time in, or patch the clock where it is used (`core/mocking.md`) |
| randomness | `random`, `uuid`, set or dict ordering of unordered data | seed it, or assert on what does not depend on it (sorted, lengths, membership) |
| network, other services | timeouts, connection errors | mock the boundary; move real calls into marked integration tests |
| files | fixed paths in `/tmp` or the project, leftovers from earlier runs | `tmp_path` |
| parallel workers | passes alone, fails with `-n` | same as shared state; a shared resource (port, database, file) per worker using the `worker_id` fixture of xdist |

5. Confirm the fix with the command that failed every time, and several
   seeds.

## Slow tests

- `uv run pytest --durations=10` lists the slowest setups, calls and
  teardowns; `--durations=0` all of them, `-vv` includes the tiny ones.
- A slow **setup** means a fixture: widen its scope only if tests do not
  change what it returns (`core/fixtures.md`).
- A slow **call**: sleeps, real network, large data. Replace the sleep
  with waiting on the condition, mock the network, shrink the data.
- Mark tests that must stay slow (`@pytest.mark.slow`, registered in the
  configuration) and deselect them in the fast run: `-m "not slow"`.
- `-n auto` (pytest-xdist) only after the suite passes with
  `-p no:randomly` and with random orders; otherwise it hides nothing and
  adds failures.

## Never

- Never add retries (`pytest-rerunfailures`, `@flaky`, loops) to make a
  test pass; it hides the cause and the bug it may be showing.
- Never "fix" order dependence by pinning the order (`-p no:randomly` in
  the configuration, ordering plugins).
- Never raise a timeout or add a `sleep` without knowing what the test
  waits for.
