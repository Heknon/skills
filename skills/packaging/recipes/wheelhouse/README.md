# Recipe: a wheelhouse for an air-gapped Windows machine

Procedure: `core/across-the-gap.md`. Lab: uv 0.12.19, pip 26.2.1,
Python 3.12; the connected side and the offline install ran on Linux with
the network cut; the Windows lines are not run on Windows.

## 1. Air-gapped side: export the lock

```
uv export --no-emit-project --no-dev -o requirements.txt
```

Carry `requirements.txt` and `fetch-wheels.sh` out.

## 2. Connected side (a person): download

```
sh fetch-wheels.sh                                   # win_amd64, CPython 3.12
TARGET_PLATFORM=manylinux_2_17_x86_64 sh fetch-wheels.sh   # add Linux wheels too
```

Lab output for a project on pydantic and click: `pydantic_core-2.46.5-
cp312-cp312-win_amd64.whl` and pure-Python wheels, plus hatchling and its
dependencies for building on the far side.

## 3. Either side: check the wheelhouse fits the target

```
uv pip compile requirements.txt --python-platform x86_64-pc-windows-msvc --python-version 3.12 --no-index --find-links wheelhouse --offline
```

It resolves (lab: exit 0), or names the package with no matching wheel:
`has no wheels with a matching platform tag (e.g., win_amd64)`.

## 4. Air-gapped side: install offline (PowerShell)

```
uv venv .venv --python 3.12
uv pip install --offline --no-index --find-links wheelhouse -r requirements.txt
uv build --offline --no-index --find-links wheelhouse
uv pip install --offline --no-index --no-deps dist\reporter-1.0.0-py3-none-any.whl
uv run --no-sync python -c "import reporter, pydantic; print(pydantic.VERSION)"
```

Lab (Linux, `dist/`): the install printed `+ pydantic==2.13.5` and the
others, the build `Successfully built dist/reporter-1.0.0-py3-none-any.whl`,
and the import `2.13.5`.
