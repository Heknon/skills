# Worked example: what changed between two versions

Kinds: Changed, Signature. Verdict: confirmed from source, with a
changelog. Commands and output from a lab run of eval `what-changed`
(Linux, uv 0.12.19, CPython 3.12.14). The `wheels\` folder stands in for
the mirror.

## The ask

> We want to upgrade fetchkit from 1.4 to 1.5 (both are in `wheels/`,
> our mirror). What changed that breaks our call in `app/client.py`?

```python
# app/client.py
def load_page(page: int) -> bytes:
    return fetchkit.get(CATALOGUE_URL, 5, params={"page": str(page)})
```

## Steps

1. **Pin the installed version**: `lookup.py pin fetchkit` printed
   `dist:      fetchkit 1.4.0`, a copy from an index.

2. **Look for a changelog** (`core/changed.md`), in the wheel first:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py wheel wheels\fetchkit-1.5.0-py3-none-any.whl
         611  fetchkit/__init__.py
          81  fetchkit-1.5.0.dist-info/WHEEL
         106  fetchkit-1.5.0.dist-info/METADATA
         284  fetchkit-1.5.0.dist-info/RECORD
   ```

   None, and the `METADATA` has no release notes. The sdist has one:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py wheel wheels\fetchkit-1.5.0.tar.gz CHANGELOG.md
   --- fetchkit-1.5.0/CHANGELOG.md
   # Changelog

   ## 1.5.0

   - `get()` takes every argument after `url` as keyword-only.
   - The `params` argument of `get()` is renamed `query`. There is no alias.
   ```

3. **Check the changelog against the code**, both wheels read in place,
   nothing installed:

   ```
   > uv run --no-sync python <skill>\recipes\lookup.py diff wheels\fetchkit-1.4.0-py3-none-any.whl wheels\fetchkit-1.5.0-py3-none-any.whl
   ...
   -def get(url, timeout=10, params=None, headers=None):
   +def get(url, *, query=None, headers=None, timeout=10):
   ...
   2 file(s) differ
   ```

   The two changes the changelog names, and no others in `get`.

4. **Match them to our call**: `get(CATALOGUE_URL, 5, params=...)` passes
   `timeout` by position (keyword-only in 1.5.0) and uses `params`
   (renamed `query`). Both break.

5. **Run our code under 1.5.0** in a throwaway environment, which leaves
   `.venv` alone (decision OD3):

   ```
   > uv run --isolated --no-project --find-links wheels --with fetchkit==1.5.0 python -c "from app.client import load_page; load_page(2)"
       return fetchkit.get(CATALOGUE_URL, 5, params={"page": str(page)})
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   TypeError: get() got an unexpected keyword argument 'params'
   ```

   The run shows only the first error; the diff shows both.
   `uv pip list` afterwards: `fetchkit 1.4.0`, unchanged.

6. **Check the new call on both versions**, against a local port so no
   request leaves the machine: under 1.5.0 `get('http://127.0.0.1:9/',
   timeout=5, query={'page': '2'})` got as far as connecting
   (`URLError: <urlopen error [Errno 111] Connection refused>`); under
   1.4.0 it raised `TypeError: get() got an unexpected keyword argument
   'query'`.

## The answer

```
## Answer
Answer:   Two changes in fetchkit 1.5.0 break app/client.py:7: every argument after
          url is keyword-only (our positional 5), and params is renamed query with
          no alias. The call becomes get(CATALOGUE_URL, timeout=5,
          query={"page": str(page)}), which 1.4.0 rejects (no query there), so
          change it together with the upgrade.
Checked:  fetchkit 1.4.0 installed; 1.5.0 from wheels/ (wheel and sdist), Python
          3.12.14, /home/user/od-lab/ex4/.venv/bin/python
Evidence: fetchkit-1.5.0.tar.gz CHANGELOG.md "## 1.5.0" lines 5-6; diff of the two
          wheels: def get(url, timeout=10, params=None, headers=None) ->
          def get(url, *, query=None, headers=None, timeout=10); run under 1.5.0:
          TypeError: get() got an unexpected keyword argument 'params'
Source:   code, and the changelog in the sdist
Verdict:  confirmed from source at fetchkit/__init__.py:9 on fetchkit 1.5.0
          (read in wheels/fetchkit-1.5.0-py3-none-any.whl)

## Not checked
- Versions after 1.5.0: not in wheels/.
- Other callers of fetchkit.get in the repository (navigation's Trace in).
```
