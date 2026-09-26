# Metadata: importlib.metadata and the .dist-info folder

**What it decides:** a distribution's version, dependencies, files,
description and install kind, read from its metadata, installed or
still in a wheel, without importing its code.

All results from CPython 3.12.14 and uv 0.12.19 (*lab*). How metadata is
built and published is the packaging skill's; this file only reads it.

## Distribution name and import name

`pip install` and `uv add` take the distribution name; `import` takes the
import name. `packages_distributions()` maps import names to
distributions:

```powershell
uv run --no-sync python -c "import importlib.metadata as md; print(md.packages_distributions().get('yaml'))"
```

| Import name | Distribution (*lab*) |
| --- | --- |
| `yaml`, `_yaml` | `['PyYAML']` (6.0.3; also in its `top_level.txt`) |
| `fetchkit-stubs` | `['types-fetchkit']` |
| `requests-stubs` | `['types-requests']` |
| an editable project's package (`ledgerlib`) | `None`: not in the map |
| `_virtualenv` | `None` |

An editable install's files are not in its `RECORD` (only the `.pth`
file is), so the map misses it. Use `find_spec` for where it loads from
(`core/pin-version.md`).

## The calls

```powershell
uv run --no-sync python -c "import importlib.metadata as md; print(md.version('orjson'))"
uv run --no-sync python -c "import importlib.metadata as md; m = md.metadata('orjson'); print(m['Summary'], m['Requires-Python'], m.get_all('Project-URL'))"
uv run --no-sync python -c "import importlib.metadata as md; print(md.requires('mypy'))"
uv run --no-sync python -c "import importlib.metadata as md; print([str(f) for f in md.files('types-fetchkit')])"
uv run --no-sync python -c "import importlib.metadata as md; print(md.distribution('ledgerlib').read_text('direct_url.json'))"
```

| Call | Lab output |
| --- | --- |
| `md.version('orjson')` | `3.12.0` |
| `m['Summary']`, `m['Requires-Python']` | the summary line, `>=3.10` |
| `m.get_all('Project-URL')` | `['changelog, https://github.com/ijl/orjson/blob/master/CHANGELOG.md', ...]`: a link, not a changelog on the machine |
| `m['Description']` | the long description, the README: 1108 lines for orjson 3.12.0 |
| `md.requires('mypy')` | `['typing_extensions>=4.6.0; python_version < "3.15"', ..., 'psutil>=4.0; extra == "dmypy"', ...]`, with markers and extras |
| `md.requires('fetchkit')` | `None` (no dependencies) |
| `md.files(...)` | the `RECORD` entries |
| `read_text('direct_url.json')` | `{"url":"file:///home/user/od-lab/editable","dir_info":{"editable":true}}` for an editable install; `None` for an index install |
| an unknown name | `importlib.metadata.PackageNotFoundError` |

Console commands (`entry_points.txt`) are listed by navigation's
`tools/terminal-probes.md`.

## The METADATA text is documentation

The body of `METADATA` is the README the authors published with that
version. It is often the best written documentation on the machine:
orjson 3.12.0's says at lines 166-168 that `sort_keys` is replaced by
`option=orjson.OPT_SORT_KEYS` and `indent` by `option=orjson.OPT_INDENT_2`.
Some carry release notes (`core/changed.md`). Search it with the recipe's
`grep`, which includes the `METADATA` of the package's distribution, or
read the file in `<dist>-<version>.dist-info\`.

It describes the release, not a guarantee: check what it says in the
code when the code is there.

## A wheel or sdist that is not installed

A wheel is a zip file; nothing needs installing to read it:

```powershell
uv run --no-sync python <skill>\recipes\lookup.py wheel wheels\fetchkit-1.5.0-py3-none-any.whl
uv run --no-sync python <skill>\recipes\lookup.py wheel wheels\fetchkit-1.5.0-py3-none-any.whl METADATA
uv run --no-sync python -m zipfile -l wheels\fetchkit-1.5.0-py3-none-any.whl
```

```
--- fetchkit-1.5.0.dist-info/METADATA
Metadata-Version: 2.3
Name: fetchkit
Version: 1.5.0
Summary: A small HTTP helper.
Requires-Python: >=3.10
```

`RECORD` inside it lists every file the wheel would install
(`fetchkit/__init__.py,sha256=...,611`). `importlib.metadata` can read the
wheel directly as well:

```powershell
uv run --no-sync python -c "import zipfile, importlib.metadata as md; d = md.PathDistribution(zipfile.Path('wheels/fetchkit-1.5.0-py3-none-any.whl', 'fetchkit-1.5.0.dist-info/')); print(d.version, [str(f) for f in d.files])"
```

printed `1.5.0 ['fetchkit/__init__.py', 'fetchkit-1.5.0.dist-info/WHEEL', ...]`.

An sdist (`.tar.gz`) holds `PKG-INFO` (the same fields as `METADATA`) and
the source tree, often with a changelog the wheel lacks:
`lookup.py wheel wheels\fetchkit-1.5.0.tar.gz CHANGELOG.md` printed it,
and `python -m tarfile -l <file>` lists it.

## Never

- Never import a package to learn its version when `md.version` answers.
- Never take a `Project-URL` for documentation you have; it is a web link.
