# Worked example: Resolve, when the change does not run

Follow this for "I changed it and nothing happened". Copy the order of the
steps and the answer shape; change the names.

## The ask

> I changed `src/greeter/core.py` to print "Hello v2", but running the
> tool still prints "Hello v1". Why?

## Steps

1. **Do not reread the source.** The source says v2; the program says v1.
   The question is which file actually runs (`core/resolve.md`, "when the
   repository and the interpreter disagree").

2. **Find the project interpreter** (`python/environment.md`): `uv.lock`
   is present, so uv, and `.venv\Scripts\python.exe`.

3. **Ask it where the module comes from** (`tools/terminal-probes.md`):

   ```
   > .venv\Scripts\python.exe -c "import importlib.util as u; print(u.find_spec('greeter.core').origin)"
   C:\work\greeter\.venv\Lib\site-packages\greeter\core.py
   ```

   Not `src\greeter\core.py`. An installed copy runs.

4. **Is it editable?**

   ```
   > .venv\Scripts\python.exe -m pip show greeter
   Name: greeter
   Version: 1.4.0
   Location: C:\work\greeter\.venv\Lib\site-packages
   ```

   No `Editable project location` line: a copy of version 1.4.0, installed
   before the change.

5. **Confirm the copy is the v1 text**: read
   `.venv\Lib\site-packages\greeter\core.py`; it prints "Hello v1".

## The answer

```
## Found
.venv\Lib\site-packages\greeter\core.py - the file that runs, an installed copy of greeter 1.4.0
src\greeter\core.py - the file you changed, which does not run

## How I know
find_spec('greeter.core').origin with the project interpreter,
.venv\Scripts\python.exe, is the site-packages copy.
pip show greeter has no Editable project location: it is a plain copy.
The copy prints "Hello v1".

To run your change, reinstall the project in editable mode, or run it with
uv run, which installs the project from source. That changes the
environment, so it is your call.

## Not covered
none
```
