# Installing and running pyright offline

**What it decides:** how pyright gets Node air gapped, and what the
errors look like when it cannot. Verified on the pyright 1.1.414 wheel,
`nodejs-wheel-binaries` 24.19.0 and basedpyright 1.40.1, with the
network cut off (a network namespace, and a dead proxy).

pyright is a Node program. The PyPI wheel carries pyright's JavaScript;
it still needs a `node` to run it. The wheel's installed `node.py`
looks, in order, for:

1. the `nodejs-wheel-binaries` package, installed by `pyright[nodejs]`
   (switch off with `PYRIGHT_PYTHON_NODEJS_WHEEL=0`);
2. `node` on `PATH` (switch off with `PYRIGHT_PYTHON_GLOBAL_NODE=0`);
3. otherwise it downloads Node with `nodeenv` into
   `~/.cache/pyright-python` (`PYRIGHT_PYTHON_CACHE_DIR` moves it).

## What each install did offline

| Install | Node on `PATH` | Result |
| --- | --- | --- |
| `pyright[nodejs]==1.1.414` | no | ran: `3 errors, 0 warnings, 1 information` |
| `pyright==1.1.414` (no extra) | yes | ran, and fetched nothing |
| `pyright==1.1.414` (no extra) | no | failed, even for `--version` |
| `basedpyright==1.40.1` | no | ran; it depends on `nodejs-wheel-binaries` itself |

The failure without Node ends with:

```
urllib.error.URLError: <urlopen error [Errno 111] Connection refused>
...
RuntimeError: nodeenv failed; for more reliable node.js binaries try `pip install pyright[nodejs]`
```

Air gapped, the host part says the name did not resolve instead of
`Connection refused`. The cure is the extra, from the mirror, in the dev
group: `pyright[nodejs]==1.1.414` (the packaging skill changes groups).
Never `pip install` it by hand; never point `PYRIGHT_PYTHON_NODE_VERSION`
or a Pylance version at the network.

`nodejs-wheel-binaries` has wheels per platform; the Windows one was not
tried here.

## basedpyright

A fork of pyright with the same command line plus `--writebaseline`,
`--baselinefile` and `--gitlabcodequality <FILE>`, the extra modes
`recommended` and `all`, and `[tool.basedpyright]`. It is what Zed
starts by default (`core/zed.md`). Use it when the project does; do not
swap one for the other inside a task, since their defaults differ
(`pyright/strictness.md`).

## Finding the project's packages

See `pyright/config.md`: run it through uv, or set `venvPath` and
`venv`. `reportMissingImports` for a package the project has means
pyright looked in another environment; `--verbose` shows where.
