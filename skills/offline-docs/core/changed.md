# Changed: what differs between versions

**Verdict you produce:** for each version, the evidence: changelog lines
quoted with the file they came from, or the lines of a diff of the two
versions' code. Never a change you remember.

```
from:     <dist> <version A> (installed | from <where>)
to:       <dist> <version B> (from <where>)
changes:  <each change, with the changelog line or the diff lines>
breaks:   <which of our calls, as path:line, and why>
```

Also for "since when does X exist" and "is X deprecated".

Pin the installed version first (`core/pin-version.md`).

## Where a changelog is, offline

A changelog is rarely installed. In a survey of 59 popular packages on the
public index (2026-09-26, latest versions):

| Place | Had release notes |
| --- | --- |
| a changelog file in the wheel (what gets installed) | 0 of 59 |
| the sdist (`.tar.gz`) | 37 of 59: `CHANGELOG.md`, `CHANGES.rst`, `HISTORY.md`, `NEWS.rst` and similar |
| the long description in `METADATA` | a few, such as pydantic 1.10.26: `## v1.10.26 (2025-12-18)` at line 110 of its `METADATA`, with every 1.10 release below it |
| neither | 22 of 59, among them boto3, numpy, pandas, fastapi, ruff |

So look in this order, and quote what you find with its file:

1. The installed `.dist-info\METADATA` (`python/metadata.md`); search it
   for the version number.
2. The sdist, if the mirror has one: list it and print the changelog
   without unpacking (`recipes/lookup.py wheel <file> CHANGELOG.md`).
3. Neither: compare the code of the two versions (below). Say "no
   changelog on the machine; compared the code".

## Getting the other version without changing the project

**Read the file.** If the wheel or sdist is on disk (a wheelhouse, a
download folder), read it as an archive; nothing is installed:

```powershell
uv run --no-sync python <skill>\recipes\lookup.py wheel wheels\fetchkit-1.5.0.tar.gz CHANGELOG.md
uv run --no-sync python <skill>\recipes\lookup.py diff wheels\fetchkit-1.4.0-py3-none-any.whl wheels\fetchkit-1.5.0-py3-none-any.whl
```

**Or run it from uv's cache** in a throwaway environment:

```powershell
uv run --isolated --no-project --with fetchkit==1.5.0 python -c "import fetchkit, os; print(fetchkit.__version__, os.path.dirname(fetchkit.__file__))"
```

*Lab*, uv 0.12.19, in the `what-changed` sandbox:

- It printed `1.5.0 /root/.cache/uv/archive-v0/FqzZL3ZT8foAYDfp/lib/python3.12/site-packages/fetchkit`:
  the second version lives in uv's cache, not in `.venv`.
- `.venv` was unchanged: the same checksum of every file before and after,
  and `uv pip freeze` still said `fetchkit==1.4.0`.
- Without `--isolated --no-project`, `uv run --no-sync --with ...` also
  imported 1.5.0 (the `--with` layer comes first) and also left `.venv`
  alone.
- The version must be on an index uv uses. Without `--find-links wheels`
  uv asked its default index, which had no 1.5.0, and said
  ``error: No solution found when resolving `--with` dependencies`` and
  `there is no version of fetchkit==1.5.0`. With the mirror as the
  default index, `--with` asks the mirror (not run against a mirror).
  With `--offline` it ran from what uv had cached.

Then compare the two folders:

```powershell
uv run --no-sync python <skill>\recipes\lookup.py diff .venv\Lib\site-packages\fetchkit <folder printed above>
```

This is the one environment an answer may create (decision OD3): say in
the answer that you ran it. Never `uv add`, `uv sync`, `uv lock` or
`uv pip install` to answer a question.

## Steps

1. Pin the installed version (A).
2. Find the target version (B): the person's words, or the newest the
   mirror has.
3. Look for a changelog, in the order above. Quote the lines for every
   version after A up to B, not only B.
4. With no changelog, or to check one, get B's code and diff it against
   A's. Read every changed `def` the question touches.
5. For "what breaks our call": find our calls (navigation's Trace in),
   and check each against B's signature (`core/signature.md`). A run
   under B shows only the first error: in eval `what-changed`,
   `load_page(2)` under 1.5.0 raised `TypeError: get() got an unexpected
   keyword argument 'params'`, while the diff shows a second break, the
   positional `5` after `url` is now keyword-only.
6. Report each change with its evidence, and say for each whether it came
   from a changelog or from the diff.

## Since when, and deprecations

- **Since when does X exist**: run the check under each version, oldest
  worth asking first, and say which versions you checked; "added in" is
  only as precise as the versions you tried:

  ```powershell
  uv run --isolated --no-project --with pkg==<v> python -c "import pkg; print(hasattr(pkg, 'X'))"
  ```

  *Lab*: `hasattr(fetchkit, 'post')` was `False` for 1.4.0 and 1.5.0 and
  `True` for 2.0.0, so `post` appeared in 2.0.0, among the versions on
  hand.

  For a standard library module, typeshed's `VERSIONS` file answers
  without running anything (`python/stubs.md`).
- **Is X deprecated**: search the installed package for the warning:
  `lookup.py grep pydantic "DeprecationWarning"` gave 7 matches in
  pydantic 1.10.26, such as `main.py:468`, where `dict(skip_defaults=...)`
  warns `"skip_defaults" is deprecated and replaced by "exclude_unset"`
  (*lab*). Quote the warning line.

## Never

- Never write "in 2.0 they renamed X" without a changelog line or a diff
  that shows it.
- Never install the other version into the project's environment.
- Never take the newest changelog's claims for an older installed version.
