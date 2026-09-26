# Worked example: a data file lost in the wheel

Kinds: Debug, Layout, Build. Copy the order of the steps and the
answer's shape. Outputs are from a lab run on uv 0.12.19 and hatchling
1.32.4.

## The ask

> notifier 0.9.0 works with `uv run notifier`, and the tests pass, but
> on the server it dies with FileNotFoundError. Fix it.

## Steps

1. **Orient** (`core/orient.md`): hatchling, src layout
   (`src/notifier/`), static version 0.9.0. `src/notifier/cli.py` reads
   `Path(__file__).parents[2] / "config" / "defaults.toml"`: a file
   outside the package, found by walking up from the source file.
2. **Reproduce with the wheel, not the checkout** (`core/verify.md`):
   ```
   uv build
   uv run --no-project python <skill>\recipes\tools\inspect_dist.py "dist\*"
   ```
   ```
   == notifier-0.9.0-py3-none-any.whl (wheel, 6 files)
     notifier/__init__.py
     notifier/cli.py
   == notifier-0.9.0.tar.gz (sdist, 7 files)
     notifier-0.9.0/config/defaults.toml
   ```
   The sdist has `config/defaults.toml`; the wheel does not, because
   only the package folder goes into a wheel. Installed by its path in a
   fresh venv and run from the temp folder:
   ```
   FileNotFoundError: [Errno 2] No such file or directory: '/tmp/nv/lib/python3.12/config/defaults.toml'
   ```
   `parents[2]` of the installed `cli.py` is `lib/python3.12`, not the
   project.
3. **First idea, tried and rejected.** `[tool.hatch.build.targets.wheel
   .force-include] "config/defaults.toml" = "notifier/defaults.toml"`,
   with the code reading `files("notifier").joinpath("defaults.toml")`,
   would put the file in the wheel, but the editable install reads
   `src/notifier/`, where the file is not: `uv run pytest` went to `1
   failed`, `FileNotFoundError: ... src/notifier/defaults.toml`. A fix
   that breaks development is not a fix.
4. **The fix:** move the file into the package and read it through the
   package, so the checkout and the wheel agree:
   - `config/defaults.toml` moved to `src/notifier/defaults.toml`;
   - `cli.py`: `tomllib.loads(files("notifier").joinpath("defaults.toml").read_text())`.
   hatchling ships every file in the package folder that `.gitignore`
   does not exclude (`backends/hatchling.md`), so no setting is needed.
5. **Check** (`core/verify.md`):
   - `uv run pytest`: `1 passed`; `uv run notifier`: `sender=noreply@example.com`.
   - `uv build --clear`, then `inspect_dist.py "dist\*" --against
     src\notifier`: `every source file is in the distribution` for the
     sdist and the wheel.
   - fresh venv, wheel by path, run from the temp folder:
     `sender=noreply@example.com`.
6. **Release:** 0.9.0 is on the server already; the fix ships as 0.9.1
   (`uv version --bump patch`). Not published: that waits for the person.

## The answer

```
## Result
The wheel never contained config/defaults.toml: a wheel holds only the
package folder, and cli.py found the file by walking up from its own
location, which only works in the checkout. Moved the file to
src/notifier/defaults.toml and read it with importlib.resources
(src/notifier/cli.py). Version bumped to 0.9.1 for the release.

## Checked
- Before: the wheel listing had no defaults.toml; installed in a fresh
  venv, `notifier` raised FileNotFoundError for .../config/defaults.toml.
- After: `uv run pytest` 1 passed; inspect_dist.py --against src/notifier:
  every source file is in the distribution (sdist and wheel); fresh venv,
  wheel by path: `sender=noreply@example.com`.
- Rejected: force-include fixed the wheel but broke the editable install
  (1 failed).

## Not checked
- Anything outside this repository that reads config/defaults.toml by
  path (deploy scripts, other services); `git grep defaults.toml` in this
  repository found only cli.py.

## Needs a person
- Publishing 0.9.1: the tag and the CI publish job.
```
